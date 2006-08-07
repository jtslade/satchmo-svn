from django.db import models
from satchmo.contact.models import Contact, Organization

class RawItem(models.Model):
    supplier = models.ForeignKey(Organization)
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
    supplier = models.ForeignKey(Organization)
    date_created = models.DateField(auto_now_add=True)
    order_subtotal = models.FloatField(max_digits=6, decimal_places=2)
    order_shipping = models.FloatField(max_digits=6, decimal_places=2)
    order_tax = models.FloatField(max_digits=6, decimal_places=2)
    order_notes = models.CharField(maxlength=200, blank=True)
    order_total = models.FloatField(max_digits=6, decimal_places=2)
    
    def __str__(self):
        return str(self.date_created)
    
    def _status(self):
        return(self.supplierorderstatus_set.latest('date').status)
    status = property(_status)  
    
    class Admin:
        list_display = ('supplier','date_created', 'order_total','status')
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
    date = models.DateTimeField(blank=True)
    
    def __str__(self):
        return str(self.status)


    

