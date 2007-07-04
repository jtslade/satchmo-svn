"""
Sets up a discount that can be applied to a product
"""

from django.db import models
from satchmo.product.models import Item
from datetime import date
from satchmo.shop.utils.validators import MutuallyExclusiveWithField
from django.utils.translation import ugettext, ugettext_lazy as _

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
        help_text=_("Enter absolute amount OR percentage"))
    percentage = models.DecimalField(_("Discount Percentage"), decimal_places=2,
        max_digits=4, blank=True, null=True,
        validator_list=[percentage_validator],
        help_text=_("Enter absolute amount OR percentage"))
    allowedUses = models.IntegerField(_("Number of allowed uses"),
        blank=True, null=True)
    numUses = models.IntegerField(_("Number of times already used"),
        blank=True, null=True)
    minOrder = models.DecimalField(_("Minimum order value"),
        decimal_places=2, max_digits=6, blank=True, null=True)
    startDate = models.DateField(_("Start Date"))
    endDate = models.DateField(_("End Date"))
    active = models.BooleanField(_("Active"))
    freeShipping = models.BooleanField(_("Free shipping"),
        help_text=_("Should this discount remove all shipping costs?"))
    validProducts = models.ManyToManyField(Item, filter_interface=True)

    def __unicode__(self):
        return self.description
    
    def isValid(self):
        #Make sure this discount still has available uses and is in the current date range
        if not self.active:
            return (False, ugettext('This coupon is disabled.'))
        if self.startDate > date.today():
            return (False, ugettext('This coupon is not active yet.'))
        if self.endDate < date.today():
            return (False, ugettext('This coupon has expired.'))
        if self.numUses > self.allowedUses:
            return (False, ugettext('This discount has exceeded the number of' +
                ' allowed uses.'))
        return (True, ugettext('Valid.'))
        
    class Admin:
        list_display=('description','active')
    
    class Meta:
        verbose_name = _("Discount")
        verbose_name_plural = _("Discounts")

