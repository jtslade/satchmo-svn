"""
Stores details about the available payment options.
Also stores credit card info in an ecrypted format.
"""

from django.db import models
from satchmo.contact.models import Order
import base64
from Crypto.Cipher import Blowfish
from django.conf import settings

# Create your models here.
PAYMENTCHOICES = (
 ('CreditCard','CreditCard'),
)

CREDITCHOICES = (
                ('Visa','Visa'),
                ('Mastercard','Mastercard'),
                ('Discover','Discover'),
                )


class PaymentOption(models.Model):
    """
    If there are multiple options - CC, Cash, COD, etc this class allows
    configuration.
    """
    description = models.CharField(maxlength=20)
    active = models.BooleanField(help_text="Should this be displayed as an option for the user?")
    optionName = models.CharField(maxlength=20, choices=PAYMENTCHOICES, unique=True, help_text="The class name as defined in payment.py")
    sortOrder = models.IntegerField()
    
    class Admin:
        list_display = ['optionName','description','active']
        ordering = ['sortOrder']
        
class CreditCardDetail(models.Model):
    """
    Stores and encrypted CC number and info as well as a displayable number
    """
    order = models.ForeignKey(Order, edit_inline=True, num_in_admin=1, max_num_in_admin=1)
    creditType = models.CharField(maxlength=16, choices=CREDITCHOICES)
    displayCC = models.CharField(maxlength=4, core=True)
    encryptedCC = models.CharField(maxlength=30, blank=True, null=True)
    expireMonth = models.IntegerField()
    expireYear = models.IntegerField()
    ccv = models.IntegerField(blank=True, null=True)
    
    
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