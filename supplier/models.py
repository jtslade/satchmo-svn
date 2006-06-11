from django.db import models

class Supplier(models.Model):
    name = models.CharField("Company Name", maxlength=100)
    address1 = models.CharField("Address 1", maxlength=150)
    address2 = models.CharField("Address 2", maxlength=150, blank=True)
    city = models.CharField("City", maxlength=100)
    state = models.USStateField("State")
    zip = models.IntegerField("Zip Code")
    phone1 = models.PhoneNumberField("Phone Number 1", blank=True, null=True)
    phone2 = models.PhoneNumberField("Phone Number 2", blank=True, null=True)
    fax = models.PhoneNumberField("Fax Number")
    email = models.EmailField("Email")
    notes = models.TextField("Notes",maxlength=500, blank=True)
    
    def __str__(self):
        return self.name
        
    class Admin:
        ordering = ['name']
        

class RawItem(models.Model):
    supplier = models.ForeignKey(Supplier)
    supplier_num = models.CharField(maxlength=50)
    description = models.CharField(maxlength=200)
    unit_cost = models.FloatField(max_digits=6, decimal_places=2)
    inventory = models.IntegerField()
    
    def __str__(self):
        return self.description
    
    class Admin:
        list_display = ('supplier','description','supplier_num','inventory',)
        list_filter = ('supplier',)
        
class SupplierOrder(models.Model):
    supplier = models.ForeignKey(Supplier)
    date_created = models.DateField(auto_now_add=True)
    order_subtotal = models.FloatField(max_digits=6, decimal_places=2)
    order_shipping = models.FloatField(max_digits=6, decimal_places=2)
    order_tax = models.FloatField(max_digits=6, decimal_places=2)
    order_notes = models.CharField(maxlength=200, blank=True)
    order_total = models.FloatField(max_digits=6, decimal_places=2)
    
    def __str__(self):
        return str(self.date_created)
    
    class Admin:
        list_display = ('supplier','date_created', 'order_total')
        list_filter = ('date_created','supplier',)
        date_hierarchy = 'date_created'
    
class SupplierOrderItem(models.Model):
    order = models.ForeignKey(SupplierOrder,edit_inline=models.TABULAR, num_in_admin=3)
    line_item = models.ForeignKey(RawItem, core=True)
    line_item_quantity = models.IntegerField(core=True)
    line_item_total = models.FloatField(max_digits=6,decimal_places=2)
    
    def __str__(self):
        return str(self.line_item_total) 

SUPPLIERORDER_STATUS = (
    ('Sent in', 'Sent in'),
    ('Shipped', 'Shipped'),
    ('Received', 'Received'),
)



class SupplierOrderStatus(models.Model):
    order = models.ForeignKey(SupplierOrder, edit_inline=models.STACKED, num_in_admin=1)
    status = models.CharField(maxlength=20, choices=SUPPLIERORDER_STATUS, core=True, blank=True)
    notes = models.CharField(maxlength=100, blank=True)
    date = models.DateField(blank=True)
    
    def __str__(self):
        return str(self.date)


    

