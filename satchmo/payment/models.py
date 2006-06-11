from django.db import models
from satchmo.customer.models import Order

# Create your models here.
PAYMENTCHOICES = (
 ('CreditCard','CreditCard'),
)


class PaymentOption(models.Model):
    description = models.CharField(maxlength=20)
    active = models.BooleanField(help_text="Should this be displayed as an option for the user?")
    optionName = models.CharField(maxlength=20, choices=PAYMENTCHOICES, unique=True, help_text="The class name as defined in payment.py")
    sortOrder = models.IntegerField()
    
    class Admin:
        list_display = ['optionName','description','active']
        ordering = ['sortOrder']
        
class CreditCardDetail(models.Model):
    order = models.ForeignKey(Order, edit_inline=True, num_in_admin=1, max_num_in_admin=1)
    ccnum = models.IntegerField(core=True)
    expireMonth = models.IntegerField()
    expireYear = models.IntegerField()
    