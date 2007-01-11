"""
Sets up a discount that can be applied to a product
"""

from django.db import models
from satchmo.product.models import Item
from datetime import date
from satchmo.shop.utils.validators import MutuallyExclusiveWithField
from django.utils.translation import gettext_lazy as _


percentage_validator = MutuallyExclusiveWithField('amount')
amount_validator = MutuallyExclusiveWithField('percentage')

class Discount(models.Model):
    """
    Allows for multiple types of discounts including % and dollar off.
    Also allows finite number of uses.
    """
    description = models.CharField(_("Description"), maxlength=100)
    code = models.CharField(_("Discount Code"), maxlength=20, help_text=_("Coupon Code"))
    amount = models.FloatField(_("Discount Amount"), decimal_places=2, max_digits=4, blank=True, null=True,
                                help_text=_("Enter absolute amount OR percentage"), validator_list=[amount_validator])
    percentage = models.FloatField(_("Discount Percentage"), decimal_places=2, max_digits=4, blank=True, 
                                    null=True, help_text=_("Enter absolute amount OR percentage"), validator_list=[percentage_validator])
    allowedUses = models.IntegerField(_("Number of allowed uses"), blank=True, null=True)
    numUses = models.IntegerField(_("Number of times already used"), blank=True, null=True)
    minOrder = models.FloatField(_("Minimum order value"), decimal_places=2, max_digits=6, blank=True, null=True)
    startDate = models.DateField(_("Start Date"))
    endDate = models.DateField(_("End Date"))
    active = models.BooleanField(_("Active"))
    freeShipping = models.BooleanField(_("Free shipping"), help_text=_("Should this discount remove all shipping costs?"))
    validProducts = models.ManyToManyField(Item, filter_interface=True)

    def __str__(self):
        return(self.description)
    
    def isValid(self):
        #Make sure this discount still has available uses and is in the current date range
        if not self.active:
            return(False, _("This coupon is not active."))
        if self.startDate > date.today():
            return(False,_("This coupon is not active yet."))
        if self.endDate < date.today():
            return(False,_("This coupon has expired"))
        if self.numUses > self.allowedUses:
            return(False,_("This discount has exceeded the number of uses."))
        return(True, _("Valid"))
        
    class Admin:
        list_display=('description','active')
    
    class Meta:
        verbose_name = _("Discount")
        verbose_name_plural = _("Disconts")