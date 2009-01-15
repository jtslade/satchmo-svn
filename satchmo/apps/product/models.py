"""
Base model used for products.  Stores hierarchical categories
as well as individual product level information which includes
options.
"""

import config
import datetime
import logging
import random
import sha
import signals
import operator
import os.path

from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.db import models
from django.db.models import Q
from django.db.models.fields.files import FileField
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, ugettext, ugettext_lazy as _
from livesettings import config_value, SettingNotSet, config_value_safe
from satchmo_utils import cross_list, normalize_dir, url_join, get_flat_list, add_month
from satchmo_utils.thumbnail.field import ImageWithThumbnailField
from satchmo_utils.unique_id import slugify

try:
    from decimal import Decimal
except:
    from django.utils._decimal import Decimal

log = logging.getLogger('product.models')

dimension_units = (('cm','cm'), ('in','in'))

weight_units = (('kg','kg'), ('lb','lb'))

SHIP_CLASS_CHOICES = (
    ('DEFAULT', _('Default')),
    ('YES', _('Shippable')),
    ('NO', _('Not Shippable'))
)

def default_dimension_unit():
    val = config_value_safe('PRODUCT','MEASUREMENT_SYSTEM', (None, None))[0]
    if val == 'metric':
        return 'cm'
    else:
        return 'in'

def default_weight_unit():
    val = config_value_safe('PRODUCT','MEASUREMENT_SYSTEM', (None, None))[0]
    if val == 'metric':
        return 'kg'
    else:
        return 'lb'

class CategoryManager(models.Manager):
    
    def by_site(self, site=None, **kwargs):
        """Get all categories for this site"""
        if not site:
            site = Site.objects.get_current()
        
        site = site.id

        return self.filter(site__id__exact = site, **kwargs)
        
    def root_categories(self, site=None, **kwargs):
        """Get all root categories."""
        
        if not site:
            site = Site.objects.get_current()
        
        return self.filter(parent__isnull=True, site=site, **kwargs)
        
    def search_by_site(self, keyword, site=None, include_children=False):
        """Search for categories by keyword. 
        Note, this does not return a queryset."""
        
        if not site:
            site = Site.objects.get_current()
        
        cats = self.filter(
            Q(name__icontains=keyword) |
            Q(meta__icontains=keyword) |
            Q(description__icontains=keyword),
            site=site)
        
        if include_children:
            # get all the children of the categories found
            cats = [cat.get_active_children(include_self=True) for cat in cats]
            
        # sort properly
        if cats:
            fastsort = [(c.ordering, c.name, c) for c in get_flat_list(cats)]
            fastsort.sort()
            # extract the cat list
            cats = zip(*fastsort)[2]            
        return cats

class Category(models.Model):
    """
    Basic hierarchical category model for storing products
    """
    site = models.ForeignKey(Site, verbose_name=_('Site'))
    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField(_("Slug"), help_text=_("Used for URLs, auto-generated from name if blank"), blank=True)
    parent = models.ForeignKey('self', blank=True, null=True,
        related_name='child')
        #,validator_list=['categoryvalidator'])
    meta = models.TextField(_("Meta Description"), blank=True, null=True,
        help_text=_("Meta description for this category"))
    description = models.TextField(_("Description"), blank=True,
        help_text="Optional")
    ordering = models.IntegerField(_("Ordering"), default=0, help_text=_("Override alphabetical order in category display"))
    related_categories = models.ManyToManyField('self', blank=True, null=True, 
        verbose_name=_('Related Categories'), related_name='related_categories')
    objects = CategoryManager()

    def _get_mainImage(self):
        img = False
        if self.images.count() > 0:
            img = self.images.order_by('sort')[0]
        else:
            if self.parent_id and self.parent != self:
                img = self.parent.main_image

        if not img:
            #This should be a "Image Not Found" placeholder image
            try:
                img = CategoryImage.objects.filter(category__isnull=True).order_by('sort')[0]
            except IndexError:
                import sys
                print >>sys.stderr, 'Warning: default category image not found - try syncdb'

        return img

    main_image = property(_get_mainImage)

    def active_products(self, variations=True, include_children=False, **kwargs):
        if not include_children:
            qry = self.product_set.all()
        else:
            cats = self.get_all_children(include_self=True)
            qry = Product.objects.filter(category__in=cats)
            
        if variations:
            return qry.filter(site=self.site, active=True, **kwargs)
        else:
            return qry.filter(site=self.site, active=True, productvariation__parent__isnull=True, **kwargs)

    def translated_description(self, language_code=None):
        return lookup_translation(self, 'description', language_code)

    def translated_name(self, language_code=None):
        return lookup_translation(self, 'name', language_code)

    def _recurse_for_parents(self, cat_obj):
        p_list = []
        if cat_obj.parent_id:
            p = cat_obj.parent
            p_list.append(p)
            if p != self:
                more = self._recurse_for_parents(p)
                p_list.extend(more)
        if cat_obj == self and p_list:
            p_list.reverse()
        return p_list
        
    def parents(self):
        return self._recurse_for_parents(self)

    def get_absolute_url(self):
        parents = self._recurse_for_parents(self)
        slug_list = [cat.slug for cat in parents]
        if slug_list:
            slug_list = "/".join(slug_list) + "/"
        else:
            slug_list = ""
        return urlresolvers.reverse('satchmo_category', 
            kwargs={'parent_slugs' : slug_list, 'slug' : self.slug})

    def get_separator(self):
        return ' :: '

    def _parents_repr(self):
        name_list = [cat.name for cat in self._recurse_for_parents(self)]
        return self.get_separator().join(name_list)
    _parents_repr.short_description = "Category parents"

    def get_url_name(self):
        # Get all the absolute URLs and names for use in the site navigation.
        name_list = []
        url_list = []
        for cat in self._recurse_for_parents(self):
            name_list.append(cat.translated_name())
            url_list.append(cat.get_absolute_url())
        name_list.append(self.translated_name())
        url_list.append(self.get_absolute_url())
        return zip(name_list, url_list)

    def __unicode__(self):
        name_list = [cat.name for cat in self._recurse_for_parents(self)]
        name_list.append(self.name)
        return self.get_separator().join(name_list)

    def save(self, force_insert=False, force_update=False):
        if self.id:
            if self.parent and self.parent_id == self.id:
                raise validators.ValidationError(_("You must not save a category in itself!"))

            for p in self._recurse_for_parents(self):
                if self.id == p.id:
                    raise validators.ValidationError(_("You must not save a category in itself!"))

        if not self.slug:
            self.slug = slugify(self.name, instance=self)

        super(Category, self).save(force_insert=force_insert, force_update=force_update)

    def _flatten(self, L):
        """
        Taken from a python newsgroup post
        """
        if type(L) != type([]): return [L]
        if L == []: return L
        return self._flatten(L[0]) + self._flatten(L[1:])

    def _recurse_for_children(self, node, only_active=False):
        children = []
        children.append(node)
        for child in node.child.all():
            if child != self:
                if (not only_active) or child.active_products().count() > 0:
                    children_list = self._recurse_for_children(child, only_active=only_active)
                    children.append(children_list)
        return children

    def get_active_children(self, include_self=False):
        """
        Gets a list of all of the children categories which have active products.
        """
        return self.get_all_children(only_active=True, include_self=include_self)

    def get_all_children(self, only_active=False, include_self=False):
        """
        Gets a list of all of the children categories.
        """
        children_list = self._recurse_for_children(self, only_active=only_active)
        if include_self:
            ix = 0
        else:
            ix = 1
        flat_list = self._flatten(children_list[ix:])
        return flat_list
        
    class Meta:
        ordering = ['site', 'parent__id', 'ordering', 'name']
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

class CategoryTranslation(models.Model):
    """A specific language translation for a `Category`.  This is intended for all descriptions which are not the
    default settings.LANGUAGE.
    """
    category = models.ForeignKey(Category, related_name="translations")
    languagecode = models.CharField(_('language'), max_length=10, choices=settings.LANGUAGES)
    name = models.CharField(_("Translated Category Name"), max_length=255, )
    description = models.TextField(_("Description of category"), default='', blank=True)
    version = models.IntegerField(_('version'), default=1)
    active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('Category Translation')
        verbose_name_plural = _('Category Translations')
        ordering = ('category', 'name','languagecode')
        unique_together = ('category', 'languagecode', 'version')

    def __unicode__(self):
        return u"CategoryTranslation: [%s] (ver #%i) %s Name: %s" % (self.languagecode, self.version, self.category, self.name)

class CategoryImage(models.Model):
    """
    A picture of an item.  Can have many pictures associated with an item.
    Thumbnails are automatically created.
    """
    category = models.ForeignKey(Category, null=True, blank=True,
        related_name="images")
    picture = ImageWithThumbnailField(verbose_name=_('Picture'),
        upload_to="__DYNAMIC__",
        name_field="_filename",
        max_length=200) #Media root is automatically prepended
    caption = models.CharField(_("Optional caption"), max_length=100,
        null=True, blank=True)
    sort = models.IntegerField(_("Sort Order"), )

    def translated_caption(self, language_code=None):
        return lookup_translation(self, 'caption', language_code)

    def _get_filename(self):
        if self.category:
            return '%s-%s' % (self.category.slug, self.id)
        else:
            return 'default'
    _filename = property(_get_filename)

    def __unicode__(self):
        if self.category:
            return u"Image of Category %s" % self.category.slug
        elif self.caption:
            return u"Image with caption \"%s\"" % self.caption
        else:
            return u"%s" % self.picture

    class Meta:
        ordering = ['sort']
        unique_together = (('category', 'sort'),)
        verbose_name = _("Category Image")
        verbose_name_plural = _("Category Images")

class CategoryImageTranslation(models.Model):
    """A specific language translation for a `CategoryImage`.  This is intended for all descriptions which are not the
    default settings.LANGUAGE.
    """
    categoryimage = models.ForeignKey(CategoryImage, related_name="translations")
    languagecode = models.CharField(_('language'), max_length=10, choices=settings.LANGUAGES)
    caption = models.CharField(_("Translated Caption"), max_length=255, )
    version = models.IntegerField(_('version'), default=1)
    active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('Category Image Translation')
        verbose_name_plural = _('Category Image Translations')
        ordering = ('categoryimage', 'caption','languagecode')
        unique_together = ('categoryimage', 'languagecode', 'version')

    def __unicode__(self):
        return u"CategoryImageTranslation: [%s] (ver #%i) %s Name: %s" % (self.languagecode, self.version, self.categoryimage, self.name)

class OptionGroupManager(models.Manager):
    def get_sortmap(self):
        """Returns a dictionary mapping ids to sort order"""
        
        work = {}
        for uid, order in self.values_list('id', 'sort_order'):
            work[uid] = order

        return work

class NullDiscount(object):

    def __init__(self):
        self.description = _("No Discount")
        self.total = Decimal("0.00")
        self.item_discounts = {}
        self.discounted_prices = []
        self.automatic = False

    def calc(self, *args):
        return Decimal("0.00")
        
    def is_valid(self):
        return False
        
    def valid_for_product(self, product):
        return False

class DiscountManager(models.Manager):
    def by_code(self, code, raises=False):
        discount = None

        if code:
            try:
                return self.get(code=code, active=True)

            except Discount.DoesNotExist:
                if raises:
                    raise
                    
        return NullDiscount()

class Discount(models.Model):
    """
    Allows for multiple types of discounts including % and dollar off.
    Also allows finite number of uses.
    """
    site = models.ForeignKey(Site, verbose_name=_('site'))
    description = models.CharField(_("Description"), max_length=100)
    code = models.CharField(_("Discount Code"), max_length=20, unique=True,
        help_text=_("Coupon Code"))
    amount = models.DecimalField(_("Discount Amount"), decimal_places=2,
        max_digits=4, blank=True, null=True, 
        #validator_list=[amount_validator],
        help_text=_("Enter absolute discount amount OR percentage."))
    percentage = models.DecimalField(_("Discount Percentage"), decimal_places=2,
        max_digits=4, blank=True, null=True,
        #validator_list=[percentage_validator],
        help_text=_("Enter absolute discount amount OR percentage.  Percentage example: \"0.10\"."))
    automatic = models.BooleanField(_("Is this an automatic discount?"), default=False, blank=True,
        null=True, help_text=_("Use this field to advertise the discount on all products to which it applies.  Generally this is used for site-wide sales."))
    allowedUses = models.IntegerField(_("Number of allowed uses"),
        blank=True, null=True, help_text=_('Not implemented.'))
    numUses = models.IntegerField(_("Number of times already used"),
        blank=True, null=True, help_text=_('Not implemented.'))
    minOrder = models.DecimalField(_("Minimum order value"),
        decimal_places=2, max_digits=6, blank=True, null=True)
    startDate = models.DateField(_("Start Date"))
    endDate = models.DateField(_("End Date"))
    active = models.BooleanField(_("Active"))
    freeShipping = models.BooleanField(_("Free shipping"), blank=True, null=True,
        help_text=_("Should this discount remove all shipping costs?"))
    includeShipping = models.BooleanField(_("Include shipping"), blank=True, null=True,
        help_text=_("Should shipping be included in the discount calculation?"))
    validProducts = models.ManyToManyField('Product', verbose_name=_("Valid Products"),
        blank=True, null=True, help_text="Make sure not to include gift certificates!")

    objects = DiscountManager()
        
    def __init__(self, *args, **kwargs):
        self._calculated = False
        super(Discount, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.description

    def isValid(self, cart=None):
        """
        Make sure this discount still has available uses and is in the current date range.
        If a cart has been populated, validate that it does apply to the products we have selected.
        """
        if not self.active:
            return (False, ugettext('This coupon is disabled.'))
        if self.startDate > datetime.date.today():
            return (False, ugettext('This coupon is not active yet.'))
        if self.endDate < datetime.date.today():
            return (False, ugettext('This coupon has expired.'))
        if self.numUses > self.allowedUses:
            return (False, ugettext('This discount has exceeded the number of allowed uses.'))
        if not cart:
            return (True, ugettext('Valid.'))

        minOrder = self.minOrder or 0
        if cart.total < minOrder:
            return (False, ugettext('This discount only applies to orders of at least %s.' % moneyfmt(minOrder)))

        validItems = False
        if self.validProducts.count() == 0:
            validItems = True
        else:
            validItems = len(self._valid_products(cart.cartitem_set))

        if validItems:
            return (True, ugettext('Valid.'))
        else:
            return (False, ugettext('This discount cannot be applied to the products in your cart.'))

    def _valid_products(self, item_query):
        validslugs = self.validProducts.values_list('slug', flat=True)
        itemslugs = item_query.values_list('product__slug', flat=True)
        return ProductPriceLookup.objects.filter(
            Q(discountable=True)
            &Q(productslug__in=validslugs)
            &Q(productslug__in=itemslugs)
            ).values_list('productslug', flat=True)

    def calc(self, order):
        # Use the order details and the discount specifics to calculate the actual discount
        discounted = {}
        if self.validProducts.count() == 0:
            allvalid = True
        else:
            allvalid = False
            validproducts = self._valid_products(order.orderitem_set)

        for lineitem in order.orderitem_set.all():
            lid = lineitem.id
            price = lineitem.line_item_price
            if lineitem.product.is_discountable and (allvalid or lineitem.product.slug in validproducts):
                discounted[lid] = price

        if self.includeShipping and not self.freeShipping:
            shipcost = order.shipping_cost
            discounted['Shipping'] = shipcost

        if self.amount:
            # perform a flat rate discount, applying evenly to all items
            # in cart
            discounted = Discount.apply_even_split(discounted, self.amount)

        elif self.percentage:
            discounted = Discount.apply_percentage(discounted, self.percentage)

        else:
            # no discount, probably shipping-only
            zero = Decimal("0.00")
            for key in discounted.keys():
                discounted[key] = zero

        if self.freeShipping:
            shipcost = order.shipping_cost
            discounted['Shipping'] = shipcost

        self._item_discounts = discounted
        self._calculated = True

    def _total(self):
        assert(self._calculated)
        return reduce(operator.add, self.item_discounts.values())
    total = property(_total)

    def _item_discounts(self):
        """Get the dictionary of orderitem -> discounts."""
        assert(self._calculated)
        return self._item_discounts
    item_discounts = property(_item_discounts)

    def _percentage_text(self):
        """Get the human readable form of the sale percentage."""
        if self.percentage > 1:
            pct = self.percentage
        else:
            pct = self.percentage*100
        cents = Decimal("0")
        pct = pct.quantize(cents)
        return "%i%%" % pct

    percentage_text = property(_percentage_text)

    def valid_for_product(self, product):
        """Tests if discount is valid for a single product"""
        if not product.is_discountable:
            return False
        p = self.validProducts.filter(id__exact = product.id)
        return p.count() > 0

    class Meta:
        verbose_name = _("Discount")
        verbose_name_plural = _("Discounts")

    def apply_even_split(cls, discounted, amount):
        log.debug('Apply even split on %s to: %s', amount, discounted)
        lastct = -1
        ct = len(discounted)
        split_discount = amount/ct

        while ct > 0:
            log.debug("Trying with ct=%i", ct)
            delta = Decimal("0.00")
            applied = Decimal("0.00")
            work = {}
            for lid, price in discounted.items():
                if price > split_discount:
                    work[lid] = split_discount
                    applied += split_discount
                else:
                    work[lid] = price
                    delta += price
                    applied += price
                    ct -= 1

            if applied >= amount - Decimal("0.01"):
                ct = 0

            if ct == lastct:
                ct = 0
            else:
                lastct = ct

            if ct > 0:
                split_discount = (amount-delta)/ct

        round_cents(work)
        return work

    apply_even_split = classmethod(apply_even_split)

    def apply_percentage(cls, discounted, percentage):
        work = {}
        if percentage > 1:
            log.warn("Correcting discount percentage, should be less than 1, is %s", percentage)
            percentage = percentage/100

        for lid, price in discounted.items():
            work[lid] = price * percentage
        round_cents(work)
        return work
        
    apply_percentage = classmethod(apply_percentage)


class OptionGroup(models.Model):
    """
    A set of options that can be applied to an item.
    Examples - Size, Color, Shape, etc
    """
    site = models.ForeignKey(Site, verbose_name=_('Site'))
    name = models.CharField(_("Name of Option Group"), max_length=50, 
        help_text=_("This will be the text displayed on the product page."))
    description = models.CharField(_("Detailed Description"), max_length=100,
        blank=True,
        help_text=_("Further description of this group (i.e. shirt size vs shoe size)."))
    sort_order = models.IntegerField(_("Sort Order"),
        help_text=_("The display order for this group."))

    objects = OptionGroupManager()

    def translated_description(self, language_code=None):
        return lookup_translation(self, 'description', language_code)

    def translated_name(self, language_code=None):
        return lookup_translation(self, 'name', language_code)

    def __unicode__(self):
        if self.description:
            return u"%s - %s" % (self.name, self.description)
        else:
            return self.name

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = _("Option Group")
        verbose_name_plural = _("Option Groups")

class OptionGroupTranslation(models.Model):
    """A specific language translation for an `OptionGroup`.  This is intended for all descriptions which are not the
    default settings.LANGUAGE.
    """
    optiongroup = models.ForeignKey(OptionGroup, related_name="translations")
    languagecode = models.CharField(_('language'), max_length=10, choices=settings.LANGUAGES)
    name = models.CharField(_("Translated OptionGroup Name"), max_length=255, )
    description = models.TextField(_("Description of OptionGroup"), default='', blank=True)
    version = models.IntegerField(_('version'), default=1)
    active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('Option Group Translation')
        verbose_name_plural = _('Option Groups Translations')
        ordering = ('optiongroup', 'name','languagecode')
        unique_together = ('optiongroup', 'languagecode', 'version')

    def __unicode__(self):
        return u"OptionGroupTranslation: [%s] (ver #%i) %s Name: %s" % (self.languagecode, self.version, self.optiongroup, self.name)


class OptionManager(models.Manager):
    def from_unique_id(self, unique_id):
        group_id, option_value = split_option_unique_id(unique_id)
        group = OptionGroup.objects.get(id=group_id)
        return Option.objects.get(option_group=group_id, value=option_value)

class Option(models.Model):
    """
    These are the actual items in an OptionGroup.  If the OptionGroup is Size, then an Option
    would be Small.
    """
    objects = OptionManager()
    option_group = models.ForeignKey(OptionGroup)
    name = models.CharField(_("Display value"), max_length=50, )
    value = models.CharField(_("Stored value"), max_length=50)
    price_change = models.DecimalField(_("Price Change"), null=True, blank=True,
        max_digits=14, decimal_places=6,
        help_text=_("This is the price differential for this option."))
    sort_order = models.IntegerField(_("Sort Order"))

    def translated_name(self, language_code=None):
        return lookup_translation(self, 'name', language_code)

    class Meta:
        ordering = ('option_group', 'sort_order', 'name')
        unique_together = (('option_group', 'value'),)
        verbose_name = _("Option Item")
        verbose_name_plural = _("Option Items")

    def _get_unique_id(self):
        return make_option_unique_id(self.option_group_id, self.value)
    unique_id = property(_get_unique_id)

    def __repr__(self):
        return u"<Option: %s>" % self.name

    def __unicode__(self):
        return u'%s: %s' % (self.option_group.name, self.name)

class OptionTranslation(models.Model):
    """A specific language translation for an `Option`.  This is intended for all descriptions which are not the
    default settings.LANGUAGE.
    """
    option = models.ForeignKey(Option, related_name="translations")
    languagecode = models.CharField(_('language'), max_length=10, choices=settings.LANGUAGES)
    name = models.CharField(_("Translated Option Name"), max_length=255, )
    version = models.IntegerField(_('version'), default=1)
    active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('Option Translation')
        verbose_name_plural = _('Option Translations')
        ordering = ('option', 'name','languagecode')
        unique_together = ('option', 'languagecode', 'version')

    def __unicode__(self):
        return u"OptionTranslation: [%s] (ver #%i) %s Name: %s" % (self.languagecode, self.version, self.option, self.name)

class ProductManager(models.Manager):
    
    def active(self, variations=True, **kwargs):
        if not variations:
            kwargs['productvariation__parent__isnull'] = True
        return self.filter(active=True, **kwargs)

    def active_by_site(self, variations=True, **kwargs):
        return self.by_site(active=True, variations=variations, **kwargs)

    def by_site(self, site=None, variations=True, **kwargs):
        if not site:
            site = Site.objects.get_current()
        
        site = site.id

        #log.debug("by_site: site=%s", site)
        if not variations:
            kwargs['productvariation__parent__isnull'] = True
        return self.filter(site__id__exact=site, **kwargs)

    def featured_by_site(self, site=None, **kwargs):
        return self.by_site(site=site, active=True, featured=True, **kwargs)

    def get_by_site(self, site=None, **kwargs):
        products = self.by_site(site=site, **kwargs)
        if len(products) == 0:
            raise Product.DoesNotExist
        else:
            return products[0]
            
    def recent_by_site(self, **kwargs):
        query = self.active_by_site(**kwargs)
        if query.count() == 0:
            query = self.active_by_site()
            
        query = query.order_by('-date_added')
        return query
    

class Product(models.Model):
    """
    Root class for all Products
    """
    site = models.ForeignKey(Site, verbose_name=_('Site'))
    name = models.CharField(_("Full Name"), max_length=255, blank=False,
        help_text=_("This is what the product will be called in the default site language.  To add non-default translations, use the Product Translation section below."))
    slug = models.SlugField(_("Slug Name"), blank=True,
        help_text=_("Used for URLs, auto-generated from name if blank"), max_length=80)
    sku = models.CharField(_("SKU"), max_length=255, blank=True, null=True,
        help_text=_("Defaults to slug if left blank"))
    short_description = models.TextField(_("Short description of product"), help_text=_("This should be a 1 or 2 line description in the default site language for use in product listing screens"), max_length=200, default='', blank=True)
    description = models.TextField(_("Description of product"), help_text=_("This field can contain HTML and should be a few paragraphs in the default site language explaining the background of the product, and anything that would help the potential customer make their purchase."), default='', blank=True)
    category = models.ManyToManyField(Category, blank=True, verbose_name=_("Category"))
    items_in_stock = models.DecimalField(_("Number in stock"),  max_digits=18, decimal_places=6, default='0')
    meta = models.TextField(_("Meta Description"), max_length=200, blank=True, null=True, help_text=_("Meta description for this product"))
    date_added = models.DateField(_("Date added"), null=True, blank=True)
    active = models.BooleanField(_("Is product active?"), default=True, help_text=_("This will determine whether or not this product will appear on the site"))
    featured = models.BooleanField(_("Featured Item"), default=False, help_text=_("Featured items will show on the front page"))
    ordering = models.IntegerField(_("Ordering"), default=0, help_text=_("Override alphabetical order in category display"))
    weight = models.DecimalField(_("Weight"), max_digits=8, decimal_places=2, null=True, blank=True)
    weight_units = models.CharField(_("Weight units"), max_length=3, null=True, blank=True) 
    #, validator_list=[weight_validator])
    length = models.DecimalField(_("Length"), max_digits=6, decimal_places=2, null=True, blank=True)
    length_units = models.CharField(_("Length units"), max_length=3, null=True, blank=True)
    #, validator_list=[length_validator])
    width = models.DecimalField(_("Width"), max_digits=6, decimal_places=2, null=True, blank=True)
    width_units = models.CharField(_("Width units"), max_length=3, null=True, blank=True)
    #, validator_list=[width_validator])
    height = models.DecimalField(_("Height"), max_digits=6, decimal_places=2, null=True, blank=True)
    height_units = models.CharField(_("Height units"), max_length=3, null=True, blank=True)
    #, validator_list=[height_validator])
    related_items = models.ManyToManyField('self', blank=True, null=True, verbose_name=_('Related Items'), related_name='related_products')
    also_purchased = models.ManyToManyField('self', blank=True, null=True, verbose_name=_('Previously Purchased'), related_name='also_products')
    total_sold = models.DecimalField(_("Total sold"),  max_digits=6, decimal_places=2, default='0')
    taxable = models.BooleanField(_("Taxable"), default=False)
    taxClass = models.ForeignKey('TaxClass', verbose_name=_('Tax Class'), blank=True, null=True, help_text=_("If it is taxable, what kind of tax?"))
    shipclass = models.CharField(_('Shipping'), choices=SHIP_CLASS_CHOICES, default="DEFAULT", max_length=10,
        help_text=_("If this is 'Default', then we'll use the product type to determine if it is shippable."))

    objects = ProductManager()

    def _get_mainCategory(self):
        """Return the first category for the product"""

        if self.category.count() > 0:
            return self.category.all()[0]
        else:
            return None

    main_category = property(_get_mainCategory)

    def _get_mainImage(self):
        img = False
        if self.productimage_set.count() > 0:
            img = self.productimage_set.order_by('sort')[0]
        else:
            # try to get a main image by looking at the parent if this has one
            p = self.get_subtype_with_attr('parent', 'product')
            if p:
                img = p.parent.product.main_image

        if not img:
            #This should be a "Image Not Found" placeholder image
            try:
                img = ProductImage.objects.filter(product__isnull=True).order_by('sort')[0]
            except IndexError:
                import sys
                print >>sys.stderr, 'Warning: default product image not found - try syncdb'

        return img

    main_image = property(_get_mainImage)
    
    def _is_discountable(self):
        p = self.get_subtype_with_attr('discountable')
        if p:
            return p.discountable
        else:
            return True
            
    is_discountable = property(_is_discountable)

    def translated_attributes(self, language_code=None):
        if not language_code:
            language_code = get_language()
        q = self.productattribute_set.filter(languagecode__exact = language_code)
        if q.count() == 0:
            q = self.productattribute_set.filter(Q(languagecode__isnull = True) | Q(languagecode__exact = ""))
        return q

    def translated_description(self, language_code=None):
        return lookup_translation(self, 'description', language_code)

    def translated_name(self, language_code=None):
        return lookup_translation(self, 'name', language_code)

    def translated_short_description(self, language_code=None):
        return lookup_translation(self, 'short_description', language_code)

    def _get_fullPrice(self):
        """
        returns price as a Decimal
        """

        subtype = self.get_subtype_with_attr('unit_price')

        if subtype:
            price = subtype.unit_price
        else:
            price = get_product_quantity_price(self, Decimal('1'))

        if not price:
            price = Decimal("0.00")
        return price

    unit_price = property(_get_fullPrice)

    def get_qty_price(self, qty):
        """
        If QTY_DISCOUNT prices are specified, then return the appropriate discount price for
        the specified qty.  Otherwise, return the unit_price
        returns price as a Decimal
        """
        subtype = self.get_subtype_with_attr('get_qty_price')
        if subtype:
            price = subtype.get_qty_price(qty)

        else:
            price = get_product_quantity_price(self, qty)
            if not price:
                price = self._get_fullPrice()

        return price
        
    def get_qty_price_list(self):
        """Return a list of tuples (qty, price)"""
        prices = Price.objects.filter(
            product__id=self.id).exclude(
            expires__isnull=False, 
            expires__lt=datetime.date.today()
        ).select_related()
        return [(price.quantity, price.dynamic_price) for price in prices]

    def in_stock(self):
        subtype = self.get_subtype_with_attr('in_stock')
        if subtype:
            return subtype.in_stock

        return self.items_in_stock > 0

    def _has_full_dimensions(self):
        """Return true if the dimensions all have units and values. Used in shipping calcs. """
        for att in ('length', 'length_units', 'width', 'width_units', 'height', 'height_units'):
            if self.smart_attr(att) is None:
                return False
        return True

    has_full_dimensions = property(_has_full_dimensions)

    def _has_full_weight(self):
        """Return True if we have weight and weight units"""
        for att in ('weight', 'weight_units'):
            if self.smart_attr(att) is None:
                return False
        return True

    has_full_weight = property(_has_full_weight)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return urlresolvers.reverse('satchmo_product',
            kwargs={'product_slug': self.slug})

    class Meta:
        ordering = ('site', 'ordering', 'name')
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        unique_together = (('site', 'sku'),('site','slug'))

    def save(self, force_insert=False, force_update=False):
        if not self.pk:
            self.date_added = datetime.date.today()

        if self.name and not self.slug:
            self.slug = slugify(self.name, instance=self)

        if not self.sku:
            self.sku = self.slug
        super(Product, self).save(force_insert=force_insert, force_update=force_update)
        ProductPriceLookup.objects.smart_create_for_product(self)

    def get_subtypes(self):
        types = []
        try:
            for key in config_value('PRODUCT', 'PRODUCT_TYPES'):
                app, subtype = key.split("::")
                try:
                    subclass = getattr(self, subtype.lower())
                    gettype = getattr(subclass, '_get_subtype')
                    subtype = gettype()
                    if not subtype in types:
                        types.append(subtype)
                except models.ObjectDoesNotExist:
                    pass
        except SettingNotSet:
            log.warn("Error getting subtypes, OK if in SyncDB")

        return tuple(types)

    get_subtypes.short_description = _("Product Subtypes")

    def get_subtype_with_attr(self, *args):
        """Get a subtype with the specified attributes.  Note that this can be chained
        so that you can ensure that the attribute then must have the specified attributes itself.

        example:  get_subtype_with_attr('parent') = any parent
        example:  get_subtype_with_attr('parent', 'product') = any parent which has a product attribute
        """
        for subtype_name in self.get_subtypes():
            subtype = getattr(self, subtype_name.lower())
            if hasattr(subtype, args[0]):
                if len(args) == 1:
                    return subtype
                else:
                    found = True
                    for attr in args[1:-1]:
                        if hasattr(subtype, attr):
                            subtype = getattr(self, attr)
                        else:
                            found = False
                            break
                    if found and hasattr(subtype, args[-1]):
                        return subtype

        return None

    def smart_attr(self, attr):
        """Retrieve an attribute, or its parent's attribute if it is null.
        Ex: to get a weight.  obj.smart_attr('weight')"""

        val = getattr(self, attr)
        if val is None:
            for subtype_name in self.get_subtypes():
                subtype = getattr(self, subtype_name.lower())

                if hasattr(subtype, 'parent'):
                    subtype = subtype.parent.product

                if hasattr(subtype, attr):
                    val = getattr(subtype, attr)
                    if val is not None:
                        break
        return val
                        
    def smart_relation(self, relation):
        """Retrieve a relation, or its parent's relation if the relation count is 0"""
        q = getattr(self, relation)
        if q.count() > 0:
            return q
        
        for subtype_name in self.get_subtypes():
            subtype = getattr(self, subtype_name.lower())

            if hasattr(subtype, 'parent'):
                subtype = subtype.parent.product

                return getattr(subtype, relation)

    def _has_variants(self):
        subtype = self.get_subtype_with_attr('has_variants')
        return subtype and subtype.has_variants

    has_variants = property(_has_variants)

    def _get_category(self):
        """
        Return the primary category associated with this product
        """
        subtype = self.get_subtype_with_attr('get_category')
        if subtype:
            return subtype.get_category

        try:
            return self.category.all()[0]
        except IndexError:
            return None

    get_category = property(_get_category)

    def _get_downloadable(self):
        """
        If this Product has any subtypes associated with it that are downloadable, then
        consider it downloadable
        """
        return self.get_subtype_with_attr('is_downloadable') is not None

    is_downloadable = property(_get_downloadable)

    def _get_subscription(self):
        """
        If this Product has any subtypes associated with it that are subscriptions, then
        consider it subscription based.
        """
        for prod_type in self.get_subtypes():
            subtype = getattr(self, prod_type.lower())
            if hasattr(subtype, 'is_subscription'):
                return True
        return False
    is_subscription = property(_get_subscription)

    def _get_shippable(self):
        """
        If this Product has any subtypes associated with it that are not
        shippable, then consider the product not shippable.
        If it is downloadable, then we don't ship it either.
        """
        if self.shipclass=="DEFAULT":
            subtype = self.get_subtype_with_attr('is_shippable')
            if subtype and not subtype.is_shippable:
                return False
            return True
        elif self.shipclass=="YES":
            return True
        else:
            return False
            
    is_shippable = property(_get_shippable)

    def add_template_context(self, context, *args, **kwargs):
        """
        Add context for the product template.
        Call the add_template_context method of each subtype and return the
        combined context.
        """
        subtypes = self.get_subtypes()
        logging.debug('subtypes = %s', subtypes)
        for subtype_name in subtypes:
            subtype = getattr(self, subtype_name.lower())
            if hasattr(subtype, 'add_template_context'):
                context = subtype.add_template_context(context, *args, **kwargs)

        return context

class ProductTranslation(models.Model):
    """A specific language translation for a `Product`.  This is intended for all descriptions which are not the
    default settings.LANGUAGE.
    """
    product = models.ForeignKey('Product', related_name="translations")
    languagecode = models.CharField(_('language'), max_length=10, choices=settings.LANGUAGES)
    name = models.CharField(_("Full Name"), max_length=255)
    description = models.TextField(_("Description of product"), help_text=_("This field can contain HTML and should be a few paragraphs explaining the background of the product, and anything that would help the potential customer make their purchase."), default='', blank=True)
    short_description = models.TextField(_("Short description of product"), help_text=_("This should be a 1 or 2 line description for use in product listing screens"), max_length=200, default='', blank=True)
    version = models.IntegerField(_('version'), default=1)
    active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('Product Translation')
        verbose_name_plural = _('Product Translations')
        ordering = ('product', 'name','languagecode')
        unique_together = ('product', 'languagecode', 'version')

    def __unicode__(self):
        return u"ProductTranslation: [%s] (ver #%i) %s Name: %s" % (self.languagecode, self.version, self.product, self.name)

def get_all_options(obj, ids_only=False):
    """
    Returns all possible combinations of options for this products OptionGroups as a List of Lists.
    Ex:
    For OptionGroups Color and Size with Options (Blue, Green) and (Large, Small) you'll get
    [['Blue', 'Small'], ['Blue', 'Large'], ['Green', 'Small'], ['Green', 'Large']]
    Note: the actual values will be instances of Option instead of strings
    """
    sublist = []
    masterlist = []
    #Create a list of all the options & create all combos of the options
    for opt in obj.option_group.select_related().all():
        for value in opt.option_set.all():
            if ids_only:
                sublist.append(value.unique_id)
            else:
                sublist.append(value)
        masterlist.append(sublist)
        sublist = []
    results = cross_list(masterlist)
    return results

class CustomProduct(models.Model):
    """
    Product which must be custom-made or ordered.
    """
    product = models.OneToOneField(Product, verbose_name=_('Product'), primary_key=True)
    downpayment = models.IntegerField(_("Percent Downpayment"), default=20)
    deferred_shipping = models.BooleanField(_('Deferred Shipping'),
        help_text=_('Do not charge shipping at checkout for this item.'),
        default=False)
    option_group = models.ManyToManyField(OptionGroup, verbose_name=_('Option Group'), blank=True,)

    def _is_shippable(self):
        return not self.deferred_shipping
    is_shippable = property(fget=_is_shippable)

    def _get_fullPrice(self):
        """
        returns price as a Decimal
        """
        return self.get_qty_price(Decimal('1'))

    unit_price = property(_get_fullPrice)

    def add_template_context(self, context, selected_options, **kwargs):
        """
        Add context for the product template.
        Return the updated context.
        """
        from product.utils import serialize_options

        context['options'] = serialize_options(self, selected_options)

        return context

    def get_qty_price(self, qty):
        """
        If QTY_DISCOUNT prices are specified, then return the appropriate discount price for
        the specified qty.  Otherwise, return the unit_price
        returns price as a Decimal
        """
        price = get_product_quantity_price(self.product, qty)
        if not price and qty == Decimal('1'): # Prevent a recursive loop.
            price = Decimal("0.00")
        elif not price:      
            price = self.product._get_fullPrice()

        return price * self.downpayment / 100

    def get_full_price(self, qty=Decimal('1')):
        """
        Return the full price, ignoring the deposit.
        """
        price = get_product_quantity_price(self.product, qty)
        if not price:
            price = self.product.unit_price

        return price

    full_price = property(fget=get_full_price)



    def _get_subtype(self):
        return 'CustomProduct'

    def __unicode__(self):
        return u"CustomProduct: %s" % self.product.name

    def get_valid_options(self):
        """
        Returns all of the valid options
        """
        return get_all_options(self, ids_only=True)

    class Meta:
        verbose_name = _('Custom Product')
        verbose_name_plural = _('Custom Products')

class CustomTextField(models.Model):
    """
    A text field to be filled in by a customer.
    """

    name = models.CharField(_('Custom field name'), max_length=40, )
    slug = models.SlugField(_("Slug"), help_text=_("Auto-generated from name if blank"),
        blank=True)
    products = models.ForeignKey(CustomProduct, verbose_name=_('Custom Fields'), 
        related_name='custom_text_fields')
    sort_order = models.IntegerField(_("Sort Order"),
        help_text=_("The display order for this group."))
    price_change = models.DecimalField(_("Price Change"), max_digits=14, 
        decimal_places=6, blank=True, null=True)

    def save(self, force_insert=False, force_update=False):
        if not self.slug:
            self.slug = slugify(self.name, instance=self)
        super(CustomTextField, self).save(force_insert=force_insert, force_update=force_update)

    def translated_name(self, language_code=None):
        return lookup_translation(self, 'name', language_code)

    class Meta:
        ordering = ('sort_order',)

class CustomTextFieldTranslation(models.Model):
    """A specific language translation for a `CustomTextField`.  This is intended for all descriptions which are not the
    default settings.LANGUAGE.
    """
    customtextfield = models.ForeignKey(CustomTextField, related_name="translations")
    languagecode = models.CharField(_('language'), max_length=10, choices=settings.LANGUAGES)
    name = models.CharField(_("Translated Custom Text Field Name"), max_length=255, )
    version = models.IntegerField(_('version'), default=1)
    active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('CustomTextField Translation')
        verbose_name_plural = _('CustomTextField Translations')
        ordering = ('customtextfield', 'name','languagecode')
        unique_together = ('customtextfield', 'languagecode', 'version')

    def __unicode__(self):
        return u"CustomTextFieldTranslation: [%s] (ver #%i) %s Name: %s" % (self.languagecode, self.version, self.customtextfield, self.name)

class ConfigurableProduct(models.Model):
    """
    Product with selectable options.
    This is a sort of virtual product that is visible to the customer, but isn't actually stocked on a shelf,
    the specific "shelf" product is determined by the selected options.
    """
    product = models.OneToOneField(Product, verbose_name=_("Product"), primary_key=True)
    option_group = models.ManyToManyField(OptionGroup, blank=True, verbose_name=_("Option Group"))
    create_subs = models.BooleanField(_("Create Variations"), default=False, help_text =_("Create ProductVariations for all this product's options.  To use this, you must first add an option, save, then return to this page and select this option."))

    def __init__self(*args, **kwargs):
        super(ConfigurableProduct, self).__init__(*args, **kwargs)

    def _get_subtype(self):
        return 'ConfigurableProduct'

    def get_all_options(self):
        """
        Returns all possible combinations of options for this products OptionGroups as a List of Lists.
        Ex:
        For OptionGroups Color and Size with Options (Blue, Green) and (Large, Small) you'll get
        [['Blue', 'Small'], ['Blue', 'Large'], ['Green', 'Small'], ['Green', 'Large']]
        Note: the actual values will be instances of Option instead of strings
        """
        sublist = []
        masterlist = []
        #Create a list of all the options & create all combos of the options
        for opt in self.option_group.all():
            for value in opt.option_set.all():
                sublist.append(value)
            masterlist.append(sublist)
            sublist = []
        return cross_list(masterlist)

    def get_valid_options(self):
        """
        Returns unique_ids from get_all_options(), but filters out Options that this
        ConfigurableProduct doesn't have a ProductVariation for.
        """
        variations = self.productvariation_set.filter(product__active='1')
        active_options = [v.unique_option_ids for v in variations]
        all_options = get_all_options(self, ids_only=True)
        return [opt for opt in all_options if self._unique_ids_from_options(opt) in active_options]

    def create_all_variations(self):
        """
        Get a list of all the optiongroups applied to this object
        Create all combinations of the options and create variations
        """
        # Create a new ProductVariation for each combination.
        for options in self.get_all_options():
            self.create_variation(options)

    def create_variation(self, options, name=u"", sku=u"", slug=u""):
        """Create a productvariation with the specified options.
        Will not create a duplicate."""
        log.debug("Create variation: %s", options)
        variations = self.get_variations_for_options(options)

        if not variations:
            # There isn't an existing ProductVariation.
            if self.product:
                site = self.product.site
            else:
                site = self.site
                
            variant = Product(site=site, items_in_stock=0, name=name)
            optnames = [opt.value for opt in options]
            if not slug:
                slug = slugify(u'%s_%s' % (self.product.slug, u'_'.join(optnames)))

            while Product.objects.filter(slug=slug).count():
                slug = u'_'.join((slug, unicode(self.product.id)))

            variant.slug = slug

            log.info("Creating variation for [%s] %s", self.product.slug, variant.slug)
            variant.save()

            pv = ProductVariation(product=variant, parent=self)
            pv.save()

            for option in options:
                pv.options.add(option)

            pv.name = name
            pv.sku = sku
            pv.save()

        else:
            variant = variations[0].product
            log.debug("Existing variant: %s", variant)
            dirty = False
            if name and name != variant.name:
                log.debug("Updating name: %s --> %s", self, name)
                variant.name = name
                dirty = True
            if sku and sku != variant.sku:
                variant.sku = sku
                log.debug("Updating sku: %s --> %s", self, sku)
                dirty = True
            if slug:
                # just in case
                slug = slugify(slug)
            if slug and slug != variant.slug:
                variant.slug = slug
                log.debug("Updating slug: %s --> %s", self, slug)
                dirty = True
            if dirty:
                log.debug("Changed existing variant, saving: %s", variant)
                variant.save()
            else:
                log.debug("No change to variant, skipping save: %s", variant)

        return variant

    def _unique_ids_from_options(self, options):
        """
        Takes an iterable of Options (or str(Option)) and outputs a sorted tuple of
        option unique ids suitable for comparing to a productvariation.option_values
        """
        optionlist = []
        for opt in options:
            if isinstance(options[0], Option):
                opt = opt.unique_id
            optionlist.append(opt)
            
        return sorted_tuple(optionlist)

    def get_product_from_options(self, options):
        """
        Accepts an iterable of either Option object or a sorted tuple of
        options ids.
        Returns the product that matches or None
        """    
        options = self._unique_ids_from_options(options)
        pv = None
        if hasattr(self, '_variation_cache'):
            pv =  self._variation_cache.get(options, None)
        else:
            for member in self.productvariation_set.all():
                if member.unique_option_ids == options:
                    pv = member
                    break
        if pv:
            return pv.product        
        return None

    def get_variations_for_options(self, options):
        """
        Returns a list of existing ProductVariations with the specified options.
        """
        variations = ProductVariation.objects.filter(parent=self)
        for option in options:
            variations = variations.filter(options=option)
        return variations

    def add_template_context(self, context, request, selected_options, default_view_tax=False, **kwargs):
        """
        Add context for the product template.
        Return the updated context.
        """
        from product.utils import productvariation_details, serialize_options

        selected_options = self._unique_ids_from_options(selected_options)
        context['options'] = serialize_options(self, selected_options)
        context['details'] = productvariation_details(self.product, default_view_tax,
            request.user)
                    
        return context

    def save(self, force_insert=False, force_update=False):
        """
        Right now this only works if you save the suboptions, then go back and choose to create the variations.
        """
        super(ConfigurableProduct, self).save()

        # Doesn't work with admin - the manipulator doesn't add the option_group
        # until after save() is called.
        if self.create_subs and self.option_group.count():
            self.create_all_variations()
            self.create_subs = False
            super(ConfigurableProduct, self).save(force_insert=force_insert, force_update=force_update)
            
        ProductPriceLookup.objects.smart_create_for_product(self.product)

    def get_absolute_url(self):
        return self.product.get_absolute_url()
        
    def setup_variation_cache(self):
        self._variation_cache = {}
        for member in self.productvariation_set.all():        
            key = member.unique_option_ids
            self._variation_cache[key] = member

    class Meta:
        verbose_name = _("Configurable Product")
        verbose_name_plural = _("Configurable Products")

    def __unicode__(self):
        return self.product.slug

def _protected_dir(instance, filename):
    raw = config_value_safe('PRODUCT', 'PROTECTED_DIR', 'images/')
    updir = normalize_dir(raw)
    return os.path.join(updir, os.path.basename(filename))

class DownloadableProduct(models.Model):
    """
    This type of Product is a file to be downloaded
    """
    product = models.OneToOneField(Product, verbose_name=_("Product"), primary_key=True)
    file = FileField(_("File"), upload_to=_protected_dir)
    num_allowed_downloads = models.IntegerField(_("Num allowed downloads"), help_text=_("Number of times link can be accessed."))
    expire_minutes = models.IntegerField(_("Expire minutes"), help_text=_("Number of minutes the link should remain active."))
    active = models.BooleanField(_("Active"), help_text=_("Is this download currently active?"), default=True)
    is_shippable = False
    is_downloadable = True

    def __unicode__(self):
        return self.product.slug

    def _get_subtype(self):
        return 'DownloadableProduct'

    def create_key(self):
        salt = sha.new(str(random.random())).hexdigest()[:5]
        download_key = sha.new(salt+smart_str(self.product.name)).hexdigest()
        return download_key

    def order_success(self, order, order_item):
        signals.subtype_order_success.send(self, product=self, order=order, subtype="download")

    class Meta:
        verbose_name = _("Downloadable Product")
        verbose_name_plural = _("Downloadable Products")

class SubscriptionProduct(models.Model):
    """
    This type of Product is for recurring billing (memberships, subscriptions, payment terms)
    """
    product = models.OneToOneField(Product, verbose_name=_("Product"), primary_key=True)
    recurring = models.BooleanField(_("Recurring Billing"), help_text=_("Customer will be charged the regular product price on a periodic basis."), default=False)
    recurring_times = models.IntegerField(_("Recurring Times"), help_text=_("Number of payments which will occur at the regular rate.  (optional)"), null=True, blank=True)
    expire_length = models.IntegerField(_("Duration"), help_text=_("Length of each billing cycle"), null=True, blank=True)
    SUBSCRIPTION_UNITS = (
        ('DAY', _('Days')),
        ('MONTH', _('Months'))
    )
    expire_unit = models.CharField(_("Expire Unit"), max_length=5, choices=SUBSCRIPTION_UNITS, default="DAY", null=False)
    SHIPPING_CHOICES = (
        ('0', _('No Shipping Charges')),
        ('1', _('Pay Shipping Once')),
        ('2', _('Pay Shipping Each Billing Cycle')),
    )
    is_shippable = models.IntegerField(_("Shippable?"), help_text=_("Is this product shippable?"), max_length=1, choices=SHIPPING_CHOICES)

    is_subscription = True

    def _get_subtype(self):
        return 'SubscriptionProduct'

    def __unicode__(self):
        return self.product.slug

    def _get_fullPrice(self):
        """
        returns price as a Decimal
        """
        return self.get_qty_price(1)

    unit_price = property(_get_fullPrice)

    def get_qty_price(self, qty, show_trial=True):
        """
        If QTY_DISCOUNT prices are specified, then return the appropriate discount price for
        the specified qty.  Otherwise, return the unit_price
        returns price as a Decimal
        
        Note: If a subscription has a trial, then we'll return the first trial price, otherwise the checkout won't
        balance and it will look like there are items to be paid on the order.
        """
        if show_trial:
            trial = self.get_trial_terms(0)
        else:
            trial = None
            
        if trial:
            price = trial.price * qty
        else:
            price = get_product_quantity_price(self.product, qty)
            if not price and qty == Decimal('1'):      # Prevent a recursive loop.
                price = Decimal("0.00")
            elif not price:      
                price = self.product._get_fullPrice()
        return price

    def recurring_price(self):
        """
        Get the non-trial price.
        """
        return self.get_qty_price(Decimal('1'), show_trial=False)

    # use order_success() and DownloadableProduct.create_key() to add user to group and perform other tasks
    def get_trial_terms(self, trial=None):
        """Get the trial terms for this subscription"""
        if trial is None:
            return self.trial_set.all().order_by('id')
        else:
            try:
                return self.trial_set.all().order_by('id')[trial]
            except IndexError:
                return None
                
    def calc_expire_date(self, date=None):
        if date is None:
            date = datetime.datetime.now()
        if self.expire_unit == "DAY":
            expiredate = date + datetime.timedelta(days=self.expire_length)
        else:
            expiredate = add_month(date, n=self.expire_length)
        
        return expiredate

    class Meta:
        verbose_name = _("Subscription Product")
        verbose_name_plural = _("Subscription Products")

class Trial(models.Model):
    """
    Trial billing terms for subscription products.
    Separating it out lets us have as many trial periods as we want.
    Note that some third party payment processors support only a limited number of trial
    billing periods.  For example, PayPal limits us to 2 trial periods, so if you are using
    PayPal for a billing option, you need to create no more than 2 trial periods for your
    product.  However, gateway based processors like Authorize.net can support as many
    billing periods as you wish.
    """
    subscription = models.ForeignKey(SubscriptionProduct)
    price = models.DecimalField(_("Price"), help_text=_("Set to 0 for a free trial.  Leave empty if product does not have a trial."), max_digits=10, decimal_places=2, null=True, )
    expire_length = models.IntegerField(_("Trial Duration"), help_text=_("Length of trial billing cycle.  Leave empty if product does not have a trial."), null=True, blank=True)

    def __unicode__(self):
        return unicode(self.price)
        
    def _occurrences(self):
        if self.expire_length:
            return int(self.expire_length/self.subscription.expire_length)
        else:
            return 0
    occurrences = property(fget=_occurrences)

    def calc_expire_date(self, date=None):
        if date is None:
            date = datetime.datetime.now()
        if self.subscription.expire_unit == "DAY":
            expiredate = date + datetime.timedelta(days=self.expire_length)
        else:
            expiredate = add_month(date, n=self.expire_length)
        
        return expiredate

    class Meta:
        ordering = ['-id']
        verbose_name = _("Trial Terms")
        verbose_name_plural = _("Trial Terms")

#class BundledProduct(models.Model):
#    """
#    This type of Product is a group of products that are sold as a set
#    NOTE: This doesn't do anything yet - it's just an example
#    """
#    product = models.OneToOneField(Product)
#    members = models.ManyToManyField(Product, related_name='parent_productgroup_set')
#

class ProductVariationManager(models.Manager):

    def by_parent(self, parent):
        """Get the list of productvariations which have the `product` as the parent"""
        return ProductVariation.objects.filter(parent=parent)

class ProductVariation(models.Model):
    """
    This is the real Product that is ordered when a customer orders a
    ConfigurableProduct with the matching Options selected

    """
    product = models.OneToOneField(Product, verbose_name=_('Product'), primary_key=True)
    options = models.ManyToManyField(Option, verbose_name=_('Options'))
    parent = models.ForeignKey(ConfigurableProduct, 
    #, validator_list=[variant_validator]
    verbose_name=_('Parent'))

    objects = ProductVariationManager()

    def _get_fullPrice(self):
        """ Get price based on parent ConfigurableProduct """
        # allow explicit setting of prices.
        #qty_discounts = self.price_set.exclude(expires__isnull=False, expires__lt=datetime.date.today()).filter(quantity__lte=1)
        try:
            qty_discounts = Price.objects.filter(product__id=self.product.id).exclude(expires__isnull=False, expires__lt=datetime.date.today())
            if qty_discounts.count() > 0:
                # Get the price with the quantity closest to the one specified without going over
                return qty_discounts.order_by('-quantity')[0].dynamic_price

            if self.parent.product.unit_price is None:
                log.warn("%s: Unexpectedly no parent.product.unit_price", self)
                return None

        except AttributeError:
            pass

        # calculate from options
        return self.parent.product.unit_price + self.price_delta()

    unit_price = property(_get_fullPrice)

    def _get_optionName(self):
        "Returns the options in a human readable form"
        if self.options.count() == 0:
            return self.parent.verbose_name
        output = self.parent.verbose_name + " ( "
        numProcessed = 0
        # We want the options to be sorted in a consistent manner
        optionDict = dict([(sub.option_group.sort_order, sub) for sub in self.options.all()])
        for optionNum in optionDict.keys().sort():
            numProcessed += 1
            if numProcessed == self.options.count():
                output += optionDict[optionNum].name
            else:
                output += optionDict[optionNum].name + "/"
        output += " )"
        return output
    full_name = property(_get_optionName)

    def _optionkey(self):
        #todo: verify ordering
        optkeys = [str(x) for x in self.options.values_list('value', flat=True).order_by('option_group__id')]
        return "::".join(optkeys)
    optionkey = property(fget=_optionkey)

    def _get_option_ids(self):
        """
        Return a sorted tuple of all the valid options for this variant.
        """
        qry = self.options.values_list('option_group__id', 'value').order_by('option_group')
        ret = [make_option_unique_id(*v) for v in qry]
        return sorted_tuple(ret)
        
    unique_option_ids = property(_get_option_ids)

    def _get_subtype(self):
        return 'ProductVariation'

    def _has_variants(self):
        return True
    has_variants = property(_has_variants)

    def _get_category(self):
        """
        Return the primary category associated with this product
        """
        return self.parent.product.category.all()[0]
    get_category = property(_get_category)

    def _check_optionParents(self):
        groupList = []
        for option in self.options.all():
            if option.option_group.id in groupList:
                return(True)
            else:
                groupList.append(option.option_group.id)
        return(False)

    def get_qty_price(self, qty):
        return get_product_quantity_price(self.product, qty, delta=self.price_delta(), parent=self.parent.product)

    def get_qty_price_list(self):
        """Return a list of tuples (qty, price)"""
        prices = Price.objects.filter(product__id=self.product.id).exclude(expires__isnull=False, expires__lt=datetime.date.today())
        if prices.count() > 0:
            # prices directly set, return them
            pricelist = [(price.quantity, price.dynamic_price) for price in prices]
        else:
            prices = self.parent.product.get_qty_price_list()
            price_delta = self.price_delta()

            pricelist = [(qty, price+price_delta) for qty, price in prices]

        return pricelist
        
    def _is_shippable(self):
        product = self.product
        parent = self.parent.product
        return ((product.shipclass == "DEFAULT" and parent.shipclass == "DEFAULT")
                or product.shipclass == 'YES')

    is_shippable = property(fget=_is_shippable)
    
    def isValidOption(self, field_data, all_data):
        raise validators.ValidationError(_("Two options from the same option group cannot be applied to an item."))

    def price_delta(self):
        price_delta = Decimal("0.00")
        for option in self.options.all():
            if option.price_change:
                price_delta += Decimal(option.price_change)
        return price_delta

    def save(self, force_insert=False, force_update=False):
        # don't save if the product is a configurableproduct
        if "ConfigurableProduct" in self.product.get_subtypes():
            log.warn("cannot add a productvariation subtype to a product which already is a configurableproduct. Aborting")
            return
            
        pvs = ProductVariation.objects.filter(parent=self.parent)
        pvs = pvs.exclude(product=self.product)
        for pv in pvs:
            if pv.unique_option_ids == self.unique_option_ids:
                return # Don't allow duplicates

        if not self.product.name:
            # will force calculation of default name
            self.name = ""

        super(ProductVariation, self).save(force_insert=force_insert, force_update=force_update)
        ProductPriceLookup.objects.smart_create_for_product(self.product)

    def _set_name(self, name):
        if not name:
            name = self.parent.product.name
            options = [option.name for option in self.options.order_by("option_group")]
            if options:
                name = u'%s (%s)' % (name, u'/'.join(options))
            log.debug("Setting default name for ProductVariant: %s", name)

        self.product.name = name
        self.product.save()

    def _get_name(self):
        return self.product.name

    name = property(fset=_set_name, fget=_get_name)

    def _set_sku(self, sku):
        if not sku:
            sku = self.product.slug
        self.product.sku = sku
        self.product.save()

    def _get_sku(self):
        return self.product.sku

    sku = property(fset=_set_sku, fget=_get_sku)

    def get_absolute_url(self):
        return self.product.get_absolute_url()

    class Meta:
        verbose_name = _("Product variation")
        verbose_name_plural = _("Product variations")

    def __unicode__(self):
        return self.product.slug
        

class ProductPriceLookupManager(models.Manager):
    
    def by_product(self, product):
        return self.get(productslug=product.slug)
    
    def delete_expired(self):
        for p in self.filter(expires__lt=datetime.date.today()):
            p.delete()
    
    def create_for_product(self, product):
        """Create a set of lookup objects for all priced quantities of the Product"""

        self.delete_for_product(product)
        pricelist = product.get_qty_price_list()
            
        objs = []
        for qty, price in pricelist:
            obj = ProductPriceLookup(productslug=product.slug, 
                siteid=product.site_id,
                active=product.active,
                price=price, 
                quantity=qty, 
                discountable=product.is_discountable,
                items_in_stock=product.items_in_stock)
            obj.save()
            objs.append(obj)
        return objs
        
    def create_for_configurableproduct(self, configproduct):
        """Create a set of lookup objects for all variations of this product"""

        objs = self.create_for_product(configproduct)
        for pv in configproduct.configurableproduct.productvariation_set.filter(product__active='1'):
            objs.extend(self.create_for_variation(pv, configproduct))
        
        return objs
        
    def create_for_variation(self, variation, parent):
        
        product = variation.product
        
        self.delete_for_product(product)
        pricelist = variation.get_qty_price_list()
            
        objs = []
        for qty, price in pricelist:
            obj = ProductPriceLookup(productslug=product.slug, 
                parentid=parent.pk,
                siteid=product.site_id,
                active=product.active,
                price=price, 
                quantity=qty, 
                key=variation.optionkey, 
                discountable=product.is_discountable,
                items_in_stock=product.items_in_stock)
            obj.save()
            objs.append(obj)
        return objs
        
    def delete_for_product(self, product):
        for obj in self.filter(productslug=product.slug):
            obj.delete()
        
    def rebuild_all(self, site=None):
        if not site:
            site = Site.objects.get_current()

        for lookup in self.filter(siteid=site.id):
            lookup.delete()

        ct = 0
        log.debug('ProductPriceLookup rebuilding all pricing')
        for p in Product.objects.active_by_site(site=site, variations=False):
            prices = self.smart_create_for_product(p)
            ct += len(prices)
        log.info('ProductPriceLookup built %i prices', ct)
            
    def smart_create_for_product(self, product):
        subtypes = product.get_subtypes()
        if 'ConfigurableProduct' in subtypes:
            return self.create_for_configurableproduct(product)
        elif 'ProductVariation' in subtypes:
            return self.create_for_variation(product.productvariation, product.productvariation.parent)
        else:
            return self.create_for_product(product)
    
class ProductPriceLookup(models.Model):
    """
    A denormalized object, used to quickly provide
    details needed for productvariation display, without way too many database hits.
    """
    siteid = models.IntegerField()
    key = models.CharField(max_length=60, null=True)
    parentid = models.IntegerField(null=True)
    productslug = models.CharField(max_length=80)
    price = models.DecimalField(max_digits=14, decimal_places=6)
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    active = models.BooleanField()
    discountable = models.BooleanField()
    items_in_stock = models.DecimalField(max_digits=18, decimal_places=6)

    objects = ProductPriceLookupManager()
    
    def _product(self):
        return Product.objects.get(slug=self.productslug)
        
    product = property(fget=_product)    
    
    def _dynamic_price(self):
        """Get the current price as modified by all listeners."""
        signals.satchmo_price_query.send(self, price=self, slug=self.productslug, discountable=self.discountable)
        return self.price

    dynamic_price = property(fget=_dynamic_price)

class ProductAttribute(models.Model):
    """
    Allows arbitrary name/value pairs (as strings) to be attached to a product.
    This is a very quick and dirty way to add extra info to a product.
    If you want more structure then this, create your own subtype to add
    whatever you want to your Products.
    """
    product = models.ForeignKey(Product)
    languagecode = models.CharField(_('language'), max_length=10, choices=settings.LANGUAGES, null=True, blank=True)
    name = models.SlugField(_("Attribute Name"), max_length=100, )
    value = models.CharField(_("Value"), max_length=255)

    class Meta:
        verbose_name = _("Product Attribute")
        verbose_name_plural = _("Product Attributes")

class Price(models.Model):
    """
    A Price!
    Separating it out lets us have different prices for the same product for different purposes.
    For example for quantity discounts.
    The current price should be the one with the earliest expires date, and the highest quantity
    that's still below the user specified (IE: ordered) quantity, that matches a given product.
    """
    product = models.ForeignKey(Product)
    price = models.DecimalField(_("Price"), max_digits=14, decimal_places=6, )
    quantity = models.DecimalField(_("Discount Quantity"), max_digits=18, 
        decimal_places=6, default='1.0', 
        help_text=_("Use this price only for this quantity or higher"))
    expires = models.DateField(_("Expires"), null=True, blank=True)
    #TODO: add fields here for locale/currency specific pricing

    def __unicode__(self):
        return unicode(self.price)

    def _dynamic_price(self):
        """Get the current price as modified by all listeners."""
        signals.satchmo_price_query.send(self, price=self)
        return self.price

    dynamic_price = property(fget=_dynamic_price)

    def save(self, force_insert=False, force_update=False):
        prices = Price.objects.filter(product=self.product, quantity=self.quantity)
        ## Jump through some extra hoops to check expires - if there's a better way to handle this field I can't think of it. Expires needs to be able to be set to None in cases where there is no expiration date.
        if self.expires:
            prices = prices.filter(expires=self.expires)
        else:
            prices = prices.filter(expires__isnull=True)
        if self.id:
            prices = prices.exclude(id=self.id)
        if prices.count():
            return #Duplicate Price

        super(Price, self).save(force_insert=force_insert, force_update=force_update)
        ProductPriceLookup.objects.smart_create_for_product(self.product)

    class Meta:
        ordering = ['expires', '-quantity']
        verbose_name = _("Price")
        verbose_name_plural = _("Prices")
        unique_together = (("product", "quantity", "expires"),)

class ProductImage(models.Model):
    """
    A picture of an item.  Can have many pictures associated with an item.
    Thumbnails are automatically created.
    """
    product = models.ForeignKey(Product, null=True, blank=True)
    picture = ImageWithThumbnailField(verbose_name=_('Picture'),
        upload_to="__DYNAMIC__",
        name_field="_filename",
        max_length=200) #Media root is automatically prepended
    caption = models.CharField(_("Optional caption"), max_length=100,
        null=True, blank=True)
    sort = models.IntegerField(_("Sort Order"), )

    def translated_caption(self, language_code=None):
        return lookup_translation(self, 'caption', language_code)

    def _get_filename(self):
        if self.product:
            return '%s-%s' % (self.product.slug, self.id)
        else:
            return 'default'
    _filename = property(_get_filename)

    def __unicode__(self):
        if self.product:
            return u"Image of Product %s" % self.product.slug
        elif self.caption:
            return u"Image with caption \"%s\"" % self.caption
        else:
            return u"%s" % self.picture

    class Meta:
        ordering = ['sort']
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")

class ProductImageTranslation(models.Model):
    """A specific language translation for a `ProductImage`.  This is intended for all descriptions which are not the
    default settings.LANGUAGE.
    """
    productimage = models.ForeignKey(ProductImage, related_name="translations")
    languagecode = models.CharField(_('language'), max_length=10, choices=settings.LANGUAGES)
    caption = models.CharField(_("Translated Caption"), max_length=255, )
    version = models.IntegerField(_('version'), default=1)
    active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('Product Image Translation')
        verbose_name_plural = _('Product Image Translations')
        ordering = ('productimage', 'caption','languagecode')
        unique_together = ('productimage', 'languagecode', 'version')

    def __unicode__(self):
        return u"ProductImageTranslation: [%s] (ver #%i) %s Name: %s" % (self.languagecode, self.version, self.productimage, self.name)

class TaxClass(models.Model):
    """
    Type of tax that can be applied to a product.  Tax
    might vary based on the type of product.  In the US, clothing could be
    taxed at a different rate than food items.
    """
    title = models.CharField(_("Title"), max_length=20,
        help_text=_("Displayed title of this tax."))
    description = models.CharField(_("Description"), max_length=30,
        help_text=_("Description of products that would be taxed."))

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _("Tax Class")
        verbose_name_plural = _("Tax Classes")

UNSET = object()

# --------------- helpers ------------------

def lookup_translation(obj, attr, language_code=None, version=-1):
    """Get a translated attribute by language.

    If specific language isn't found, returns the attribute from the base object.
    """
    if not language_code:
        language_code = get_language()

    if not hasattr(obj, '_translationcache'):
        obj._translationcache = {}

    short_code = language_code
    pos = language_code.find('_')
    if pos > -1:
        short_code = language_code[:pos]

    else:
        pos = language_code.find('-')
        if pos > -1:
            short_code = language_code[:pos]

    trans = None
    has_key = obj._translationcache.has_key(language_code)
    if has_key:
        if obj._translationcache[language_code] == None and short_code != language_code:
            return lookup_translation(obj, attr, short_code)

    if not has_key:
        q = obj.translations.filter(
            languagecode__iexact = language_code)

        if q.count() == 0:
            obj._translationcache[language_code] = None

            if short_code != language_code:
                return lookup_translation(obj, attr, language_code=short_code, version=version)

            else:
                q = obj.translations.filter(
                    languagecode__istartswith = language_code)

        if q.count() > 0:
            trans = None
            if version > -1:
                trans = q.order_by('-version')[0]
            else:
                # try to get the requested version, if it is available,
                # else fallback to the most recent version
                fallback = None
                for t in q.order_by('-version'):
                    if not fallback:
                        fallback = t
                    if t.version == version:
                        trans = t
                        break
                if not trans:
                    trans = fallback

            obj._translationcache[language_code] = trans

    if not trans:
        trans = obj._translationcache[language_code]

    if not trans:
        trans = obj

    val = getattr(trans, attr, UNSET)
    if trans != obj and (val in (None, UNSET)):
        val = getattr(obj, attr)

    return mark_safe(val)

def get_product_quantity_price(product, qty=Decimal('1'), delta=Decimal("0.00"), parent=None):
    """
    Returns price as a Decimal else None.
    First checks the product, if none, then checks the parent.
    """

    qty_discounts = product.price_set.exclude(expires__isnull=False, expires__lt=datetime.date.today()).filter(quantity__lte=qty)
    if qty_discounts.count() > 0:
        # Get the price with the quantity closest to the one specified without going over
        val = qty_discounts.order_by('-quantity')[0].dynamic_price
        try:
            if not type(val) is Decimal:
                val = Decimal(val)
            return val+delta
        except TypeError:
            return val+delta
    else:
        if parent:
            return get_product_quantity_price(parent, qty, delta=delta)
        return None

def make_option_unique_id(groupid, value):
    return '%s-%s' % (str(groupid), str(value),)

def round_cents(work):
    cents = Decimal("0.01")
    for lid in work:
        work[lid] = work[lid].quantize(cents)

def sorted_tuple(lst):
    ret = []
    for x in lst:
        if not x in ret:
            ret.append(x)
    ret.sort()
    return tuple(ret)

def split_option_unique_id(uid):
    "reverse of make_option_unique_id"

    parts = uid.split('-')
    return (parts[0], '-'.join(parts[1:]))
