"""
Stores details about the available payment options.
Also stores credit card info in an ecrypted format.
"""

from django.db import models
from satchmo.contact.models import Order
import base64
from Crypto.Cipher import Blowfish
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# Create your models here.
PAYMENTCHOICES = (
 (_('CreditCard'),_('CreditCard')),
)

CREDITCHOICES = (
                (_('Visa'),_('Visa')),
                (_('Mastercard'),_('Mastercard')),
                (_('Discover'),_('Discover')),
                )


class PaymentOption(models.Model):
    """
    If there are multiple options - CC, Cash, COD, etc this class allows
    configuration.
    """
    description = models.CharField(_("Description"), maxlength=20)
    active = models.BooleanField(_("Active"), help_text=_("Should this be displayed as an option for the user?"))
    optionName = models.CharField(_("Option Name"), maxlength=20, choices=PAYMENTCHOICES, unique=True, help_text=_("The class name as defined in payment.py"))
    sortOrder = models.IntegerField(_("Sort Order"))
    
    class Admin:
        list_display = ['optionName','description','active']
        ordering = ['sortOrder']
    
    class Meta:
        verbose_name = "Payment Option"
        verbose_name_plural = "Payment Options"
        
class CreditCardDetail(models.Model):
    """
    Stores and encrypted CC number and info as well as a displayable number
    """
    order = models.ForeignKey(Order, edit_inline=True, num_in_admin=1, max_num_in_admin=1)
    creditType = models.CharField(_("Credit Card Type"), maxlength=16, choices=CREDITCHOICES)
    displayCC = models.CharField(_("CC Number(Last 4 digits)"), maxlength=4, core=True)
    encryptedCC = models.CharField(_("Encrypted Credit Card"), maxlength=30, blank=True, null=True, editable=False)
    expireMonth = models.IntegerField(_("Expiration Month"))
    expireYear = models.IntegerField(_("Expiration Year"))
    ccv = models.IntegerField(_("CCV"), blank=True, null=True)
    
    
    def storeCC(self, ccnum):
        # Take as input a valid cc, encrypt it and store the last 4 digits in a visible form
        # Must remember to save it after calling!
        secret_key = settings.SECRET_KEY
        encryption_object = Blowfish.new(secret_key)
        self.encryptedCC = base64.b64encode(encryption_object.encrypt(ccnum))
        self.displayCC = ccnum[-4:]
    
    def _decryptCC(self):
        secret_key = settings.SECRET_KEY
        encryption_object = Blowfish.new(secret_key)
        return(encryption_object.decrypt(base64.b64decode(self.encryptedCC)))
    decryptedCC = property(_decryptCC) 

    def _expireDate(self):
        return(str(self.expireMonth) + "/" + str(self.expireYear))
    expirationDate = property(_expireDate)
    
    class Meta:
        verbose_name = _("Credit Card")
        verbose_name_plural = _("Credit Cards")