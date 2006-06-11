from django.db import models
from satchmo.product.models import Sub_Item
# Create your models here.

class Customer(models.Model):
    first_name = models.CharField(maxlength=30, core=True)
    last_name = models.CharField(maxlength=30, core=True)
    dob = models.DateField(blank=True, null=True)
    phone = models.CharField(blank=True, maxlength=30)
    fax=models.PhoneNumberField(blank=True)
    email=models.EmailField(blank=True)
    notes=models.TextField("Notes",maxlength=500, blank=True)
    create_date = models.DateField(auto_now_add=True)
    
    def _get_full_name(self):
        "Returns the person's full name."
        return '%s %s' % (self.first_name, self.last_name)
    full_name = property(_get_full_name)
    
    def _shipping_address(self):
        for address in self.addressbook_set.all():
            if address.is_default_shipping: 
                return(address)
        return(None)
    shipping_address = property(_shipping_address)
    
    def _billing_address(self):
        for address in self.addressbook_set.all():
            if address.is_default_billing: 
                return(address)
        return(None)
    billing_address = property(_billing_address)
    
    def __str__(self):
        return (self.full_name)
        
    class Admin:
        list_display = ('last_name','first_name')
        list_filter = ['create_date']
        ordering = ['last_name']
        
class AddressBook(models.Model):
    customer=models.ForeignKey(Customer,edit_inline=models.STACKED, num_in_admin=1)
    description=models.CharField("Description", maxlength=20,core=True,help_text='Description of address - Home,Relative, Office, Warehouse ,etc.',)
    street1=models.CharField("Street",maxlength=50)
    street2=models.CharField("Street", maxlength=50, blank=True)
    city=models.CharField("City", maxlength=50)
    state=models.USStateField("State")
    zip_code=models.CharField("Zip Code", maxlength=50)
    country=models.CharField("Country", maxlength=50, blank=True)
    is_default_shipping=models.BooleanField("Default Shipping Address ?", default=False)
    is_default_billing=models.BooleanField("Default Billing Address ?", default=False)

    def __str__(self):
       return ("%s - %s" % (self.customer.full_name, self.description))
       
    def save(self):
        """
        If the new address is the default and there already was a default billing or shipping address
        set the old one to False - we only want 1 default for each.
        If there are none, then set this one to default to both
        """
        existingBilling = self.customer.billing_address
        existingShipping = self.customer.shipping_address
        
        #If we're setting shipping & one already exists set old one to false & save it
        if self.is_default_shipping and existingShipping:
            existingShipping.is_default_shipping = False
            super(AddressBook, existingShipping).save()
        #If we're setting billing & one already exists set old one to false and save it
        if self.is_default_billing and existingBilling:
            existingBilling.is_default_billing = False
            super(AddressBook, existingBilling).save()
            
        if not existingBilling:
            self.is_default_billing = True
        if not existingShipping:
            self.is_default_shipping = True
        super(AddressBook, self).save()
        


# Create your models here.

ORDER_CHOICES = (
    ('Online', 'Online'),
    ('In Person', 'In Person'),
    ('Show', 'Show'),
)

ORDER_STATUS = (
    ('Pending', 'Pending'),
    ('Shipped', 'Shipped'),
)

PAYMENT_CHOICES = (
    ('Cash','Cash'),
    ('Credit Card','Credit Card'),
    ('Check','Check'),
)

class Order(models.Model):
    """
    Orders need to contain a copy of all the information at the time the order is placed.
    A users address or other info could change over time.
    """
    customer = models.ForeignKey(Customer)
    shipStreet1=models.CharField("Street",maxlength=50, blank=True)
    shipStreet2=models.CharField("Street", maxlength=50, blank=True)
    shipCity=models.CharField("City", maxlength=50, blank=True)
    shipState=models.USStateField("State", blank=True)
    shipZip_code=models.CharField("Zip Code", maxlength=50, blank=True)
    shipCountry=models.CharField("Country", maxlength=50, blank=True)
    billStreet1=models.CharField("Street",maxlength=50, blank=True)
    billStreet2=models.CharField("Street", maxlength=50, blank=True)
    billCity=models.CharField("City", maxlength=50, blank=True)
    billState=models.USStateField("State", blank=True)
    billZip_code=models.CharField("Zip Code", maxlength=50, blank=True)
    billCountry=models.CharField("Country", maxlength=50, blank=True)
    total = models.FloatField(max_digits=6,decimal_places=2)
    payment= models.CharField(choices=PAYMENT_CHOICES, maxlength=25)
    method = models.CharField(choices=ORDER_CHOICES, maxlength=50)
    shippingCost = models.FloatField(max_digits=6, decimal_places=2)
    tax = models.FloatField(max_digits=6, decimal_places=2)
    date = models.DateTimeField()
    
    def __str__(self):
        return self.customer.full_name
    
    def copyAddresses(self):
        """
        Copy the address so we know what the information was at time of order
        """
        shipaddress = self.customer.shipping_address
        billaddress = self.customer.billing_address
        self.shipStreet1 = shipaddress.street1
        self.shipStreet2 = shipaddress.street2
        self.shipCity = shipaddress.city
        self.shipState = shipaddress.state
        self.shipZip_code = shipaddress.zip_code
        self.shipCountry = shipaddress.country
        self.billStreet1 = billaddress.street1
        self.billStreet2 = billaddress.street2
        self.billCity = billaddress.city
        self.billState = billaddress.state
        self.billZip_code = billaddress.zip_code
        self.billCountry = billaddress.country
        
    def _status(self):
        return(self.supplierorderstatus_set.latest('date').status)
    status = property(_status)        
    
    def save(self):
        self.copyAddresses()
        super(Order, self).save() # Call the "real" save() method.
        
    class Admin:
        fields = (
        (None, {'fields': ('customer','method',)}),
        ('Shipping Information', {'fields': ('shipStreet1','shipStreet2', 'shipCity','shipState', 'shipZip_code','shipCountry',), 'classes': 'collapse'}),
        ('Billing Information', {'fields': ('billStreet1','billStreet2', 'billCity','billState', 'billZip_code','billCountry',), 'classes': 'collapse'}),
        ('Totals', {'fields': ( 'shippingCost', 'tax','total','date','payment',),}),       
        )
        list_display = ('customer', 'date', 'total','status')
        list_filter = ['date','customer']
        date_hierarchy = 'date'
    class Meta:
        verbose_name = "Product Order"
        
class OrderItem(models.Model):
    order = models.ForeignKey(Order, edit_inline=models.TABULAR, num_in_admin=3)
    item = models.ForeignKey(Sub_Item)
    quantity = models.IntegerField(core=True)
    unitPrice = models.FloatField(max_digits=6,decimal_places=2)
    lineItemPrice = models.FloatField(max_digits=6,decimal_places=2)
    
    def __str__(self):
        return self.item.full_name

class OrderStatus(models.Model):
    order = models.ForeignKey(Order, edit_inline=models.STACKED, num_in_admin=1)
    status = models.CharField(maxlength=20, choices=ORDER_STATUS, core=True, blank=True)
    notes = models.CharField(maxlength=100, blank=True)
    date = models.DateTimeField(blank=True)
    
    def __str__(self):
        return self.status
 

