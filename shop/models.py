from django.db import models


class Config(models.Model):
    """
    Used to store specific information about a store.  Also used to 
    configure various store behaviors
    """
    storeName = models.CharField("Store Name",maxlength=100, unique=True)
    storeDescription = models.TextField(blank=True)
    street1=models.CharField("Street",maxlength=50)
    street2=models.CharField("Street", maxlength=50, blank=True)
    city=models.CharField("City", maxlength=50)
    state=models.USStateField("State")
    zip_code=models.CharField("Zip Code", maxlength=9)
    country=models.CharField("Country", maxlength=50, blank=True)
    phone = models.PhoneNumberField(blank=True)
    noStockCheckout = models.BooleanField("Purchase item not in stock?")
    
    def __str__(self):
        return self.storeName
        
    class Admin:
        pass