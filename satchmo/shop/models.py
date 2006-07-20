from django.db import models
from satchmo.product.models import Item, Sub_Item
from django.contrib.sites.models import Site
from satchmo.customer.models import Customer

class Config(models.Model):
    """
    Used to store specific information about a store.  Also used to 
    configure various store behaviors
    """
    site = models.ForeignKey(Site)
    storeName = models.CharField("Store Name",maxlength=100, unique=True)
    storeDescription = models.TextField(blank=True)
    street1=models.CharField("Street",maxlength=50, blank=True, null=True)
    street2=models.CharField("Street", maxlength=50, blank=True, null=True)
    city=models.CharField("City", maxlength=50, blank=True, null=True)
    state=models.USStateField("State", blank=True, null=True)
    zip_code=models.CharField("Zip Code", blank=True, null=True,maxlength=9)
    country=models.CharField("Country", maxlength=50, blank=True, null=True)
    phone = models.PhoneNumberField(blank=True, null=True)
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
    customer = models.ForeignKey(Customer, blank=True, null=True)
    
    def _get_count(self):
        itemCount = 0
        for item in self.cartitem_set.all():
            itemCount += item.quantity
        return (itemCount)
    numItems = property(_get_count)
    
    def __str__(self):
        return ("Shopping Cart (%s)" % self.date_time_created)
    
    def add_item(self, chosen_item, number_added):
        try:
            itemToModify =  self.cartitem_set.filter(subItem__id = chosen_item.id)[0]
        except IndexError:
            itemToModify = CartItem(cart=self, subItem=chosen_item, quantity=0)
        itemToModify.quantity += number_added
        itemToModify.save()

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
        