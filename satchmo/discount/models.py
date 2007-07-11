"""
Sets up a discount that can be applied to a product
"""

from django.db import models
from satchmo.product.models import Item
from datetime import date
from satchmo.shop.utils.validators import MutuallyExclusiveWithField
from django.utils.translation import ugettext, ugettext_lazy as _
from decimal import Decimal

percentage_validator = MutuallyExclusiveWithField('amount')
amount_validator = MutuallyExclusiveWithField('percentage')

class Discount(models.Model):
    """
    Allows for multiple types of discounts including % and dollar off.
    Also allows finite number of uses.
    """
    description = models.CharField(_("Description"), maxlength=100)
    code = models.CharField(_("Discount Code"), maxlength=20, help_text=_("Coupon Code"))
    amount = models.DecimalField(_("Discount Amount"), decimal_places=2,
        max_digits=4, blank=True, null=True, validator_list=[amount_validator],
        help_text=_("Enter absolute discount amount OR percentage"))
    percentage = models.DecimalField(_("Discount Percentage"), decimal_places=2,
        max_digits=4, blank=True, null=True,
        validator_list=[percentage_validator],
        help_text=_("Enter absolute discount amount OR percentage.  Percentage example: 0.10"))
    allowedUses = models.IntegerField(_("Number of allowed uses"),
        blank=True, null=True)
    numUses = models.IntegerField(_("Number of times already used"),
        blank=True, null=True)
    minOrder = models.DecimalField(_("Minimum order value"),
        decimal_places=2, max_digits=6, blank=True, null=True)
    startDate = models.DateField(_("Start Date"))
    endDate = models.DateField(_("End Date"))
    active = models.BooleanField(_("Active"))
    freeShipping = models.BooleanField(_("Free shipping"), blank=True, null=True,
        help_text=_("Should this discount remove all shipping costs?"))
    includeShipping = models.BooleanField(_("Include shipping"), blank=True, null=True,
        help_text=_("Should shipping be included in the discount calculation?"))
    validProducts = models.ManyToManyField(Item, filter_interface=True)

    def __unicode__(self):
        return self.description
    
    def isValid(self, cart=None):
        """
        Make sure this discount still has available uses and is in the current date range.
        If a cart has been populated, validate that it does apply to the products we have selected.
        """
        if not self.active:
            return (False, ugettext('This coupon is disabled.'))
        if self.startDate > date.today():
            return (False, ugettext('This coupon is not active yet.'))
        if self.endDate < date.today():
            return (False, ugettext('This coupon has expired.'))
        if self.numUses > self.allowedUses:
            return (False, ugettext('This discount has exceeded the number of' +
                ' allowed uses.'))
        if not cart:
            return (True, ugettext('Valid.'))
        #Check to see if the cart items are included
        validItems = False
        validProducts = self.validProducts.all()
        for cart_item in cart.cartitem_set.all():
            if cart_item.subItem.item in validProducts:
                validItems = True
                break   #Once we have 1 valid item, we exit
        if validItems:
            return (True, ugettext('Valid.'))
        else:
            return (False, ugettext('This discount can not be applied to the products in your cart.'))
        
    def calc(self, order):
        # Use the order details and the discount specifics to calculate the actual discount
        if self.amount:
            return(self.amount)
        if self.percentage and self.includeShipping:
            return(self.percentage * (order.sub_total + order.shippingCost))
        if self.percentage:
            return((self.percentage * order.sub_total))
        
    class Admin:
        list_display=('description','active')
    
    class Meta:
        verbose_name = _("Discount")
        verbose_name_plural = _("Discounts")

