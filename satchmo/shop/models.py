"""
Configuration items for the shop.
Also contains shopping cart and related classes.
"""

import datetime
from decimal import Decimal
from django.contrib.sites.models import Site
from django.conf import settings
from django.db import models
from satchmo.product.models import ConfigurableProduct, Product
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_unicode
from satchmo.contact.models import Contact
from satchmo.i18n.models import Country

class Config(models.Model):
    """
    Used to store specific information about a store.  Also used to
    configure various store behaviors
    """
    site = models.OneToOneField(Site)
    store_name = models.CharField(_("Store Name"),max_length=100, unique=True)
    store_description = models.TextField(_("Description"), blank=True, null=True)
    store_email = models.EmailField(_("Email"), blank=True, null=True)
    street1=models.CharField(_("Street"),max_length=50, blank=True, null=True)
    street2=models.CharField(_("Street"), max_length=50, blank=True, null=True)
    city=models.CharField(_("City"), max_length=50, blank=True, null=True)
    state=models.CharField(_("State"), max_length=30, blank=True, null=True)
    postal_code=models.CharField(_("Zip Code"), blank=True, null=True, max_length=9)
    country=models.ForeignKey(Country, blank=True, null=True)
    phone = models.CharField(_("Phone Number"), blank=True, null=True, max_length=12)
    no_stock_checkout = models.BooleanField(_("Purchase item not in stock?"))
    in_country_only = models.BooleanField(_("Only sell to in-country customers?"), default=True)
    sales_country = models.ForeignKey(Country, blank=True, null=True,
                                     related_name='sales_country',
                                     verbose_name=_("Default country for customers"))

    def __unicode__(self):
        return self.store_name

    class Admin:
        pass

    class Meta:
        verbose_name = _("Store Configuration")
        verbose_name_plural = _("Store Configurations")

class Cart(models.Model):
    """
    Store items currently in a cart
    The desc isn't used but it is needed to make the admin interface work appropriately
    Could be used for debugging
    """
    desc = models.CharField(_("Description"), blank=True, null=True, max_length=10)
    date_time_created = models.DateTimeField(_("Creation Date"))
    customer = models.ForeignKey(Contact, blank=True, null=True)

    def _get_count(self):
        itemCount = 0
        for item in self.cartitem_set.all():
            itemCount += item.quantity
        return (itemCount)
    numItems = property(_get_count)

    def _get_total(self):
        total = Decimal("0")
        for item in self.cartitem_set.all():
            total += item.line_total
        return(total)
    total = property(_get_total)

    def __iter__(self):
        return iter(self.cartitem_set.all())

    def __len__(self):
        return self.cartitem_set.count()

    def __unicode__(self):
        return u"Shopping Cart (%s)" % self.date_time_created

    def add_item(self, chosen_item, number_added):
        try:
            itemToModify =  self.cartitem_set.filter(product__id = chosen_item.id)[0]
        except IndexError: #It doesn't exist so create a new one
            itemToModify = CartItem(cart=self, product=chosen_item, quantity=0)
        itemToModify.quantity += number_added
        itemToModify.save()

    def remove_item(self, chosen_item_id, number_removed):
        itemToModify =  self.cartitem_set.get(id = chosen_item_id)
        itemToModify.quantity -= number_removed
        if itemToModify.quantity <= 0:
            itemToModify.delete()
        self.save()

    def empty(self):
        for item in self.cartitem_set.all():
            item.delete()
        self.save()

    def save(self):
        """Ensure we have a date_time_created before saving the first time."""
        if not self.id:
            self.date_time_created = datetime.datetime.now()
        super(Cart, self).save()

    def _get_shippable(self):
        """Return whether the cart contains shippable items."""
        for cartitem in self.cartitem_set.all():
            if cartitem.product.is_shippable:
                return True
        return False
    is_shippable = property(_get_shippable)

    class Admin:
        list_display = ('date_time_created','numItems','total')

    class Meta:
        verbose_name = _("Shopping Cart")
        verbose_name_plural = _("Shopping Carts")

class CartItem(models.Model):
    """
    An individual item in the cart
    """
    cart = models.ForeignKey(Cart, edit_inline=models.TABULAR, num_in_admin=3)
    product = models.ForeignKey(Product)
    quantity = models.IntegerField(_("Quantity"), core=True)

    def _get_line_unitprice(self):
        # Get the qty discount price as the unit price for the line.
        return self.product.get_qty_price(self.quantity)
    unit_price = property(_get_line_unitprice)

    def _get_line_total(self):
        return self.unit_price * self.quantity
    line_total = property(_get_line_total)

    def _get_description(self):
        return self.product.name
    description = property(_get_description)

    def __unicode__(self):
        return u'%s - %s %s%s' % (self.quantity, self.product.name,
            force_unicode(settings.CURRENCY), self.line_total)

    class Admin:
        pass

