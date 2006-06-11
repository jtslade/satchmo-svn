from django.db import models

class Discount(models.Model):
    description = models.CharField(maxlength=100)
    code = models.CharField(maxlength=20, help_text="Coupon Code")
    amount = models.FloatField("Discount Amount", decimal_places=2, max_digits=4, blank=True)
    percentage = models.FloatField("Discount Percentage", decimal_places=2, max_digits=4, blank=True, null=True)
    allowedUses = models.IntegerField("Number of allowed uses", blank=True, null=True)
    startDate = models.DateField()
    endDate = models.DateField()
    active = models.BooleanField()
    
    def __str__(self):
        return(self.description)
    
    class Admin:
        pass