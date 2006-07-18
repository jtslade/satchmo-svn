from django.db import models
from satchmo.product.models import Item, Sub_Item

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

class Cart(models.Model):
    """
    Store items currently in a cart
    The desc isn't used but it is needed to make the admin interface work appropriately
    Could be used for debugging
    """
    desc = models.CharField(blank=True, null=True, maxlength=10)
    date_time_created = models.DateTimeField(auto_now_add=True)
    #need user info here too
    
    def _get_count(self):
        return (self.cartitem_set.count())
    numItems = property(_get_count)
    
    def __str__(self):
        return ("Shopping Cart (%s)" % self.date_time_created)
        
    class Admin:
        list_display = ('date_time_created','numItems')

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, edit_inline=models.TABULAR, num_in_admin=3)
    subItem = models.ForeignKey(Sub_Item, blank=True, null=True)
    quantity = models.IntegerField(core=True)
    
    def __str__(self):
        return("%s - %s" % (self.quantity, self.subItem.full_name))

    class Admin:
        pass
        