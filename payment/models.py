from django.db import models

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
        
    # Need to validate that each optionName