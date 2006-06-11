from django.db import models
from satchmo.product.models import Item

class Discount(models.Model):
    description = models.CharField(maxlength=100)
    code = models.CharField(maxlength=20, help_text="Coupon Code")
    amount = models.FloatField("Discount Amount", decimal_places=2, max_digits=4, blank=True, help_text="Enter absolute amount OR percentage")
    percentage = models.FloatField("Discount Percentage", decimal_places=2, max_digits=4, blank=True, null=True, help_text="Enter absolute amount OR percentage")
    allowedUses = models.IntegerField("Number of allowed uses", blank=True, null=True)
    numUses = models.IntegerField("Number of times already used", blank=True, null=False)
    minOrder = models.FloatField("Minimum order value", decimal_places=2, max_digits=6, blank=True, null=True)
    startDate = models.DateField()
    endDate = models.DateField()
    active = models.BooleanField()
    freeShipping = models.BooleanField(help_text="Should this discount remove all shipping costs?")
    validProducts = models.ManyToManyField(Item, filter_interface=True)

    def __str__(self):
        return(self.description)
    
    class Admin:
        list_display=('description','active')