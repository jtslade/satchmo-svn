"""
Helper models used to control available shipping choices through the
admin interface.
"""
from django.db import models

# Create your models here.

#This needs to contain all the valid classes from shipping-helpers
SHIPPINGCHOICES = (
 ('FlatRate','FlatRate'),
 ('PerItem','PerItem'),
)


class ShippingOption(models.Model):
    """
    Used to control which options as defined in the shipping.modules file
    are active.
    """
    description = models.CharField(maxlength=20)
    active = models.BooleanField(help_text="Should this be displayed as an option for the user?")
    optionName = models.CharField(maxlength=20, choices=SHIPPINGCHOICES, unique=True, help_text="The class name as defined in shipping.py")
    sortOrder = models.IntegerField()
    # Will need to use eval(optionName()) to instantiate each object
    class Admin:
        list_display = ['optionName','description','active']
        ordering = ['sortOrder']
