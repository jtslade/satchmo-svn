"""
Base model used for products.  Stores hierarchical categories
as well as individual product level information which includes
options.
"""

import datetime
import os
from sets import Set
from decimal import Decimal
from django.conf import settings
from django.core import validators
from django.db import models
from django.utils.translation import gettext_lazy as _
from satchmo.tax.models import TaxClass
from satchmo.thumbnail.field import ImageWithThumbnailField

class Category(models.Model):
    """
    Basic hierarchical category model for storing products
    """
    name = models.CharField(_("Name"), core=True, maxlength=200)
    slug = models.SlugField(prepopulate_from=('name',),help_text=_("Used for URLs"))
    parent = models.ForeignKey('self', blank=True, null=True, related_name='child')
    meta = models.TextField(_("Meta Description"), blank=True, null=True, help_text=_("Meta description for this category"))
    description = models.TextField(_("Description"), blank=True,help_text="Optional")
        
    def _recurse_for_parents_slug(self, cat_obj):
        #This is used for the urls
        p_list = []
        if cat_obj.parent_id:
            p = cat_obj.parent
            p_list.append(p.slug)
            more = self._recurse_for_parents_slug(p)
            p_list.extend(more)
        if cat_obj == self and p_list:
            p_list.reverse()
        return p_list

    def get_absolute_url(self):
        p_list = self._recurse_for_parents_slug(self)
        p_list.append(self.slug)
        baseurl = settings.SHOP_BASE + "/category/"
        return baseurl + "/".join(p_list)        
                
    def _recurse_for_parents_name(self, cat_obj):
        #This is used for the visual display & save validation
        p_list = []
        if cat_obj.parent_id:
            p = cat_obj.parent
            p_list.append(p.name)
            more = self._recurse_for_parents_name(p)
            p_list.extend(more)
        if cat_obj == self and p_list:
            p_list.reverse()
        return p_list
                
    def get_separator(self):
        return ' :: '
        
    def _parents_repr(self):
        p_list = self._recurse_for_parents_name(self)
        return self.get_separator().join(p_list)
    _parents_repr.short_description = "Category parents"
    
    def _recurse_for_parents_name_url(self, cat_obj):
        #Get all the absolute urls and names (for use in site navigation)
        p_list = []
        url_list = []
        if cat_obj.parent_id:
            p = cat_obj.parent
            p_list.append(p.name)
            url_list.append(p.get_absolute_url())
            more, url = self._recurse_for_parents_name_url(p)
            p_list.extend(more)
            url_list.extend(url)
        if cat_obj == self and p_list:
            p_list.reverse()
            url_list.reverse()
        return p_list, url_list

    def get_url_name(self):
        #Get a list of the url to display and the actual urls
        p_list, url_list = self._recurse_for_parents_name_url(self)
        p_list.append(self.name)
        url_list.append(self.get_absolute_url())
        return zip(p_list, url_list)
    
    def __str__(self):
        p_list = self._recurse_for_parents_name(self)
        p_list.append(self.name)
        return self.get_separator().join(p_list)
        
    def save(self):
        p_list = self._recurse_for_parents_name(self)
        if self.name in p_list:
            raise validators.ValidationError(_("You must not save a category in itself!"))
        super(Category, self).save()
        
    def _flatten(self, L):
        """
        Taken from a python newsgroup post
        """
        if type(L) != type([]): return [L]
        if L == []: return L
        return self._flatten(L[0]) + self._flatten(L[1:])
            
    def _recurse_for_children(self, node):
        children = []
        children.append(node)
        for child in node.child.all():
            children_list = self._recurse_for_children(child)
            children.append(children_list)
        return(children)

    def get_all_children(self):
        """
        Gets a list of all of the children categories.
        """
        children_list = self._recurse_for_children(self)
        flat_list = self._flatten(children_list[1:])
        return(flat_list)
    
    class Admin:
        list_display = ('name', '_parents_repr')
        ordering = ['name']
        
    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

class OptionGroup(models.Model):
    """
    A set of options that can be applied to an item.
    Examples - Size, Color, Shape, etc
    """
    name = models.CharField(_("Name of Option Group"),maxlength = 50, core=True, help_text=_('This will be the text displayed on the product page'),)
    description = models.CharField(_("Detailed Description"),maxlength = 100, blank=True, help_text=_('Further description of this group i.e. shirt size vs shoe size'),)
    sort_order = models.IntegerField(_("Sort Order"), help_text=_("The order they will be displayed on the screen"))
    
    def __str__(self):
        if self.description:
            return ("%s - %s" % (self.name, self.description))
        else:
            return self.name
    
    class Admin:
        pass
        
    class Meta:
        ordering = ['sort_order']
        verbose_name = _("Option Group")
        verbose_name_plural = _("Option Groups")
        
class Item(models.Model):
    """
    The basic product being sold in the store.  This is what the customer sees.
    """
    category = models.ManyToManyField(Category, filter_interface=True)
    verbose_name = models.CharField(_("Full Name"), maxlength=255)
    short_name = models.SlugField(_("Slug Name"), prepopulate_from=("verbose_name",), unique=True, help_text=_("This is a short, descriptive name of the shirt that will be used in the URL link to this item"))
    description = models.TextField(_("Description of product"), help_text=_("This field can contain HTML and should be a few paragraphs explaining the background of the product, and anything that would help the potential customer make their purchase."))
    meta = models.TextField(maxlength=200, blank=True, null=True, help_text=_("Meta description for this item"))
    date_added = models.DateField(null=True, blank=True)
    active = models.BooleanField(_("Is product active?"), default=True, help_text=_("This will determine whether or not this product will appear on the site"))
    featured = models.BooleanField(_("Featured Item"), default=False, help_text=_("Featured items will show on the front page"))
    option_group = models.ManyToManyField(OptionGroup, filter_interface=True, blank=True)
    base_price = models.DecimalField(_("Default Price"), max_digits=6, decimal_places=2)
    weight = models.DecimalField(_("Weight"), max_digits=6, decimal_places=2, null=True, blank=True)
    length = models.DecimalField(_("Length"), max_digits=6, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(_("Width"), max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(_("Height"), max_digits=6, decimal_places=2, null=True, blank=True)
    create_subs = models.BooleanField(_("Create Sub Items"), default=False, help_text=_("Create new sub-items"))
    relatedItems = models.ManyToManyField('self', blank=True, null=True, related_name='related')
    alsoPurchased = models.ManyToManyField('self', blank=True, null=True, related_name='previouslyPurchased')
    taxable = models.BooleanField(default=False)
    taxClass = models.ForeignKey(TaxClass, blank=True, null=True, help_text=_("If it is taxable, what kind of tax?"))    
    
    def __str__(self):
        return self.short_name 
    
    def _get_price(self):
        return self.base_price
    price = property(_get_price)
    
    def _get_mainImage(self):
        if self.itemimage_set.count() > 0:
            return(self.itemimage_set.order_by('sort')[0])
        else:
            return(False)
    main_image = property(_get_mainImage)
    
    def _cross_list(self, sequences):
        """
        Code taken from the Python cookbook v.2 (19.9 - Looping through the cross-product of multiple iterators)
        This is used to create all the sub items associated with an item
        """
        result =[[]]
        for seq in sequences:
            result = [sublist+[item] for sublist in result for item in seq]
        return result
    
    def create_subitems(self):
        """
        Get a list of all the optiongroups applied to this object
        Create all combinations of the options and create subitems
        """
        sublist = []
        masterlist = []
        #Create a list of all the options & create all combos of the options
        for opt in self.option_group.all():
            for value in opt.optionitem_set.all():
                sublist.append(value)
            masterlist.append(sublist)
            sublist = []
        combinedlist = self._cross_list(masterlist)
        #Create new sub_items for each combo
        num = 0 #used to make subitem_id unique
        for options in combinedlist:
            num += 1
            price_delta = 0
            sub = SubItem(item=self, items_in_stock=0)
            sub.subitem_id = '%s-%i' % (self.short_name, num) #TODO: there must be a better way to do this
            sub.save()
            s1 = Set()
            for option in options:
                sub.options.add(option)
                optionValue = "%s-%s" % (option.optionGroup.id, option.value)
                s1.add(optionValue)
                sub.save()
            #If the option already exists, lets make sure there are no dupes
            #TODO: Check before we create the item
            if self.get_sub_item_count(s1) > 1:              
                sub.delete()
        return(True)
    
    def get_sub_item(self, optionSet):
        for sub in self.subitem_set.all():
            if sub.option_values == optionSet:
                return(sub)
        return(None)
    
    def get_sub_item_count(self, optionSet):
        count = 0
        for sub in self.subitem_set.all():
            if sub.option_values == optionSet:
                count+=1
        return count
    
    
    def save(self):
        """Right now this only works if you save the suboptions, then go back and choose to create the subitems.
        Also ensure that we have a date_added on the first save."""
        if not self.id:
            self.date_added = datetime.date.today()

        if self.create_subs:
            self.create_subitems()
            self.create_subs = False
        super(Item, self).save()
    
    
    def get_absolute_url(self):
        return "%s/product/%s" % (settings.SHOP_BASE,self.short_name)

    
    class Admin: 
        list_display = ('verbose_name', 'active')
        fields = (
        (None, {'fields': ('category','verbose_name','short_name','description','date_added','active','featured','base_price',)}),
        ('Meta Data', {'fields': ('meta',), 'classes': 'collapse'}),
        ('Item Dimensions', {'fields': (('length', 'width','height',),'weight'), 'classes': 'collapse'}),
        ('Options', {'fields': ('option_group','create_subs',),}), 
        ('Tax', {'fields':('taxable', 'taxClass'), 'classes': 'collapse'}),
        ('Related Products', {'fields':('relatedItems','alsoPurchased'),'classes':'collapse'}), 
        )
        list_filter = ('category',)
        
    class Meta:
        verbose_name = _("Master Product")
        verbose_name_plural = _("Master Products")
        
class ItemImage(models.Model):
    """
    A picture of an item.  Can have many pictures associated with an item.
    Thumbnails are automatically created.
    """
    item = models.ForeignKey(Item, edit_inline=models.TABULAR, num_in_admin=3)
    picture = ImageWithThumbnailField(upload_to="./images") #Media root is automatically appended
    caption = models.CharField(_("Optional caption"),maxlength=100,null=True, blank=True)
    sort = models.IntegerField(_("Sort Order"), help_text=_("Leave blank to delete"), core=True)
    
    def __str__(self):
        return "Picture of %s" % self.item.short_name
        
    class Meta:
        ordering = ['sort']
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")
        
class OptionItem(models.Model):
    """
    These are the actual items in an OptionGroup.  If the OptionGroup is Size, then an OptionItem
    would be Small.
    """
    optionGroup = models.ForeignKey(OptionGroup, edit_inline=models.TABULAR, num_in_admin=5)
    name = models.CharField(_("Display value"), maxlength = 50, core=True)
    value = models.CharField(_("Stored value"), prepopulate_from=("name",), maxlength = 50)
    price_change = models.DecimalField(_("Price Change"), null=True, blank=True, 
                                    help_text=_("This is the price differential for this option"), max_digits=4, decimal_places=2)
    displayOrder = models.IntegerField(_("Display Order"))

    def _get_combined_id(self):
        return '%s-%s' % (str(self.optionGroup.id), str(self.value),)
    # optionGroup.id-value
    combined_id = property(_get_combined_id)
    
    def _get_price_change(self):
        return self.price_change
    get_price_change = property(_get_price_change)

    def __str__(self):
        return self.name
        
    class Meta:
        ordering = ['displayOrder']
        verbose_name = _("Option Item")
        verbose_name_plural = _("Option Items")
        
class SubItem(models.Model):
    """
    The unique inventoriable item.  For instance, if a shirt has a size and color, then
    only 1 SubItem would have Size=Small and Color=Black
    """
    item = models.ForeignKey(Item)
    subitem_id = models.SlugField(_("Slug Name"), unique=True, core=True)
    items_in_stock = models.IntegerField(_("Number in stock"), core=True)
    weight = models.DecimalField(_("Weight"), max_digits=6, decimal_places=2, null=True, blank=True)
    length = models.DecimalField(_("Length"), max_digits=6, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(_("Width"), max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(_("Height"), max_digits=6, decimal_places=2, null=True, blank=True)
    options = models.ManyToManyField(OptionItem, filter_interface=True, null=True, blank=True, core=True)
    
    def _get_optionName(self):
        "Returns the options in a human readable form"
        if self.options.count() == 0:
            return self.item.verbose_name
        output = self.item.verbose_name + " ( "
        numProcessed = 0
        # We want the options to be sorted in a consistent manner
        optionDict = dict([(sub.optionGroup.sort_order, sub) for sub in self.options.all()])
        for optionNum in sorted(optionDict.keys()):
            numProcessed += 1
            if numProcessed == self.options.count():
                output += optionDict[optionNum].name
            else:
                output += optionDict[optionNum].name + "/"
        output += " )"
        return output
    full_name = property(_get_optionName)
    
    def _get_fullPrice(self):
        """
        returns price as a Decimal
        """
        qty_price = self._get_qty_price(1) #get unit price for subitem if available
        if qty_price:
            return qty_price
        price_delta = Decimal('0.00') #otherwise fallback on item.price - option.price_change
        for option in self.options.all():
            if option.price_change:
                price_delta += option.get_price_change
        return self.item.price + price_delta
    unit_price = property(_get_fullPrice)
    
    def get_qty_price(self, qty):
        """
        If QTY_DISCOUNT prices are specified, then return the appropriate discount price for
        the specified qty.  Otherwise, return the unit_price
        returns price as a Decimal
        """
        qty_price = self._get_qty_price(qty)
        if qty_price:
            return qty_price
        else:
            return self.unit_price

    def _get_qty_price(self, qty):
        """
        returns price as a Decimal
        """
        qty_discounts = self.price_set.exclude(expires__isnull=False, expires__lt=datetime.date.today()).filter(quantity__lte=qty)
        if qty_discounts.count() > 0:
            # Get the price with the quantity closest to the one specified without going over
            return qty_discounts.order_by('-quantity')[0].price
        else:
            return None
    
    def _get_optionValues(self):
        """
        Return a set of all the valid options for this sub item.  
        A set makes sure we don't have to worry about ordering
        """
        output = Set()
        for option in self.options.all():
            outvalue = "%s-%s" % (option.optionGroup.id,option.value)
            output.add(outvalue)
        return(output)
    option_values = property(_get_optionValues)
    
    def _check_optionParents(self):
        groupList = []
        for option in self.options.all():
            if option.optionGroup.id in groupList:
                return(True)
            else:
                groupList.append(option.optionGroup.id)
        return(False)
            
    
    def in_stock(self):
        if self.items_in_stock > 0:
            return True
        else:
            return False;

    def __str__(self):
        return self.full_name
    
    def isValidOption(self, field_data, all_data):
        raise validators.ValidationError, _("Two options from the same option group can not be applied to an item.")
    
    #def save(self):
    #    super(Sub_Item, self).save()
    #    if self._check_optionParents():
    #        super(Sub_Item, self).delete()
    #        raise validators.ValidationError, "Two options from the same option group can not be applied to an item."
    #    else:
    #        super(Sub_Item, self).save()
    
    def get_absolute_url(self):
        return "%s/product/%s/%s/" % (settings.SHOP_BASE,self.item.short_name,self.id)

    class Admin:
        list_display = ('full_name', 'unit_price', 'items_in_stock')
        list_filter = ('item',)
        fields = (
        (None, {'fields': ('item','subitem_id','items_in_stock',)}),
        ('Item Dimensions', {'fields': (('length', 'width','height',),'weight'), 'classes': 'collapse'}),
        ('Options', {'fields': ('options',),}),       
        )

    class Meta:
        verbose_name = _("Individual Product")
        verbose_name_plural = _("Individual Products")

class Price(models.Model):
    """
    A Price!
    Separating it out lets us have different prices for the same product for different purposes.
    For example for quantity discounts.
    The current price should be the one with the earliest expires date, and the highest quantity
    that's still below the user specified (IE: ordered) quantity, that matches a given subitem.
    """
    subitem = models.ForeignKey(SubItem, edit_inline=models.TABULAR, num_in_admin=2)
    price = models.DecimalField(_("Price"), max_digits=6, decimal_places=2, core=True)
    quantity = models.IntegerField(_("Discount Quantity"), default=1, help_text=_("Use this price only for this quantity or higher"))
    expires = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.price)

    def save(self):
        #make sure that the combination of quantity/expires is unique for a given subitem.
        prices = Price.objects.filter(subitem=self.subitem, quantity=self.quantity)
        ## Jump through some extra hoops to check expires - if there's a better way to handle this field I can't think of it. Expires needs to be able to be set to None in cases where there is no expiration date.
        if self.expires:
            prices = prices.filter(expires=self.expires)
        else:
            prices = prices.filter(expires__isnull=True)
        if prices.exclude(id=self.id).count():
            return

        super(Price, self).save()

    class Meta:
        ordering = ['expires', '-quantity']
        verbose_name = _("Price")
        verbose_name_plural = _("Prices")

    class Admin:
        pass
