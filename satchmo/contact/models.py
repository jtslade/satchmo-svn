"""
Stores Customer and Order information
"""

from django.db import models
from django.contrib.auth.models import User 
from satchmo.product.models import SubItem
from django.utils.translation import gettext_lazy as _
from satchmo.shop.templatetags.currency_filter import moneyfmt
from django.conf import settings
import sys
activeShippingModules = []

#Load the shipping modules to populate the choices
#None is passed in, since all we need is the id
for module in settings.SHIPPING_MODULES:
    __import__(module)
    shipping_module = sys.modules[module]
    activeShippingModules.append((shipping_module.Calc(None,None).id,shipping_module.Calc(None,None).id))

CONTACT_CHOICES = (
    (_('Customer'), _('Customer')),
    (_('Supplier'), _('Supplier')),
    (_('Distributor'), _('Distributor')),
)

ORGANIZATION_CHOICES = (
    (_('Company'), _('Company')),
    (_('Government'),_('Government')),
    (_('Non-profit'),_('Non-profit')),
)

ORGANIZATION_ROLE_CHOICES = (
    (_('Supplier'),_('Supplier')),
    (_('Distributor'),_('Distributor')),
    (_('Manufacturer'),_('Manufacturer')),

)
class Organization(models.Model):
    """
    An organization can be a company, government or any kind of group to 
    collect contact info.
    """
    name = models.CharField(_("Name"), maxlength=50, core=True)
    type = models.CharField(_("Type"), maxlength=30,choices=ORGANIZATION_CHOICES)
    role = models.CharField(_("Role"), maxlength=30,choices=ORGANIZATION_ROLE_CHOICES)
    create_date = models.DateField(_("Creation Date"), auto_now_add=True)
    notes = models.TextField(_("Notes"), maxlength=200, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Admin:
        list_filter = ['type','role']
        list_display = ['name','type','role']
    
    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        
class Contact(models.Model):
    """
    A customer, supplier or any individual that a store owner might interact with.
    """
    first_name = models.CharField(_("First Name"), maxlength=30, core=True)
    last_name = models.CharField(_("Last Name"), maxlength=30, core=True)
    user = models.ForeignKey(User, unique=True, blank=True, null=True, edit_inline=models.TABULAR, 
                            num_in_admin=1,min_num_in_admin=1, max_num_in_admin=1,num_extra_on_change=0)
    role = models.CharField(_("Role"), maxlength=20, blank=True, null=True, choices=CONTACT_CHOICES)
    organization = models.ForeignKey(Organization, blank=True, null=True)
    dob = models.DateField(_("Date of Birth"), blank=True, null=True)   
    email = models.EmailField(_("Email"), blank=True)
    notes = models.TextField(_("Notes"),maxlength=500, blank=True)
    create_date = models.DateField(_("Creation Date"), auto_now_add=True)
    
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
    
    def _primary_phone(self):
        for phonenum in self.phonenumber_set.all():
            if phonenum.primary:
                return(phonenum)
        return(None)
    primary_phone = property(_primary_phone)
    
    def __str__(self):
        return (self.full_name)
        
    class Admin:
        list_display = ('last_name','first_name','organization','role')
        list_filter = ['create_date', 'role', 'organization']
        ordering = ['last_name']
    
    class Meta:
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")

PHONE_CHOICES = (
    (_('Work'), _('Work')),
    (_('Home'), _('Home')),
    (_('Fax'), _('Fax')),
    (_('Mobile'),_('Mobile')),
)

INTERACTION_CHOICES = (
    (_('Email'),_('Email')),
    (_('Phone'),_('Phone')),
    (_('In-person'),_('In-person')),
)

class Interaction(models.Model):
    """
    A type of activity with the customer.  Useful to track emails, phone calls or
    in-person interactions.
    """
    contact = models.ForeignKey(Contact)
    type = models.CharField(_("Type"), maxlength=30,choices=INTERACTION_CHOICES)
    date_time = models.DateTimeField(_("Date and Time"), core=True)
    description = models.TextField(_("Description"), maxlength=200)
    
    def __str__(self):
        return ("%s - %s" % (self.contact.full_name, self.type))
    
    class Admin:
        list_filter = ['type', 'date_time']
        
    class Meta:
        verbose_name = _("Interaction")
        verbose_name_plural = _("Interactions")
     
class PhoneNumber(models.Model):
    """
    Multiple phone numbers can be associated with a contact.  Cell, Home, Business etc.
    """
    contact = models.ForeignKey(Contact,edit_inline=models.TABULAR, num_in_admin=1)
    type = models.CharField(_("Description"), choices=PHONE_CHOICES, maxlength=20)
    phone = models.CharField(_("Phone Number"), blank=True, maxlength=12, core=True)
    primary = models.BooleanField(_("Primary"), default=False)
    
    def __str__(self):
        return ("%s - %s" % (self.type, self.phone))
    
    class Meta:
        unique_together = (("contact", "primary"),)
        ordering = ['-primary']
        verbose_name = _("Phone Number")
        verbose_name_plural = _("Phone Numbers")
        
class AddressBook(models.Model):
    """
    Address information associated with a contact.
    """
    contact=models.ForeignKey(Contact,edit_inline=models.STACKED, num_in_admin=1)
    description=models.CharField(_("Description"), maxlength=20,help_text=_('Description of address - Home,Relative, Office, Warehouse ,etc.',))
    street1=models.CharField(_("Street"),core=True, maxlength=50)
    street2=models.CharField(_("Street"), maxlength=50, blank=True)
    city=models.CharField(_("City"), maxlength=50)
    state=models.CharField(_("State"), maxlength=10)
    postalCode=models.CharField(_("Zip Code"), maxlength=10)
    country=models.CharField(_("Country"), maxlength=50, blank=True)
    is_default_shipping=models.BooleanField(_("Default Shipping Address"), default=False)
    is_default_billing=models.BooleanField(_("Default Billing Address"), default=False)

    def __str__(self):
       return ("%s - %s" % (self.contact.full_name, self.description))
       
    def save(self):
        """
        If the new address is the default and there already was a default billing or shipping address
        set the old one to False - we only want 1 default for each.
        If there are none, then set this one to default to both
        """
        try:
            existingBilling = self.contact.billing_address
            existingShipping = self.contact.shipping_address
        except:
            existingBilling = None
            existingShipping = None
        
        #If we're setting shipping & one already exists remove previous default
        if self.is_default_shipping and existingShipping:
            #existingShipping.delete()
            existingShipping.is_default_shipping = False
            existingShipping.save()
        #If we're setting billing & one already exists remove previous default
        if self.is_default_billing and existingBilling:
            #existingBilling.delete()
            existingBilling.is_default_billing = False
            existingBilling.save()
        if not existingBilling:
            self.is_default_billing = True
        if not existingShipping:
            self.is_default_shipping = True
        super(AddressBook, self).save()
        
        class Meta:
            verbose_name = _("Address Book")
            verbose_name_plural = _("Address Books")


ORDER_CHOICES = (
    (_('Online'), _('Online')),
    (_('In Person'), _('In Person')),
    (_('Show'), _('Show')),
)

ORDER_STATUS = (
    (_('Temp'), _('Temp')),
    (_('Pending'), _('Pending')),
    (_('In Process'), _('In Process')),
    (_('Shipped'), _('Shipped')),
)

PAYMENT_CHOICES = (
    (_('Cash'),_('Cash')),
    (_('Credit Card'),_('Credit Card')),
    (_('Check'),_('Check')),
)

class Order(models.Model):
    """
    Orders need to contain a copy of all the information at the time the order is placed.
    A user's address or other info could change over time.
    """
    contact = models.ForeignKey(Contact)
    shipStreet1=models.CharField(_("Street"),maxlength=50, blank=True)
    shipStreet2=models.CharField(_("Street"), maxlength=50, blank=True)
    shipCity=models.CharField(_("City"), maxlength=50, blank=True)
    shipState=models.CharField(_("State"), maxlength=10, blank=True)
    shipPostalCode=models.CharField(_("Zip Code"), maxlength=10, blank=True)
    shipCountry=models.CharField(_("Country"), maxlength=50, blank=True)
    billStreet1=models.CharField(_("Street"),maxlength=50, blank=True)
    billStreet2=models.CharField(_("Street"), maxlength=50, blank=True)
    billCity=models.CharField(_("City"), maxlength=50, blank=True)
    billState=models.CharField(_("State"), maxlength=10, blank=True)
    billPostalCode=models.CharField(_("Zip Code"), maxlength=10, blank=True)
    billCountry=models.CharField(_("Country"), maxlength=50, blank=True)
    notes = models.TextField(_("Notes"), maxlength=100, blank=True, null=True)
    sub_total = models.FloatField(_("Sub total"), max_digits=6, decimal_places=2, blank=True, null=True)
    total = models.FloatField(_("Total"), max_digits=6,decimal_places=2, blank=True, null=True)
    discount = models.FloatField(_("Discount"), max_digits=6, decimal_places=2, blank=True, null=True)
    payment= models.CharField(_("Payment"), choices=PAYMENT_CHOICES, maxlength=25, blank=True)
    method = models.CharField(_("Payment method"), choices=ORDER_CHOICES, maxlength=50, blank=True)
    shippingDescription = models.CharField(_("Shipping Description"), maxlength=50, blank=True, null=True)
    shippingMethod = models.CharField(_("Shipping Method"), maxlength=50, blank=True, null=True)
    shippingModel = models.CharField(_("Shipping Models"), choices=activeShippingModules, maxlength=30, blank=True, null=True)
    shippingCost = models.FloatField(_("Shipping Cost"), max_digits=6, decimal_places=2, blank=True, null=True)
    tax = models.FloatField(_("Tax"), max_digits=6, decimal_places=2, blank=True, null=True)
    timeStamp = models.DateTimeField(_("Time Stamp"), blank=True, null=True, auto_now_add=True)
    status = models.CharField(_("Status"), maxlength=20, choices=ORDER_STATUS, core=True, blank=True, help_text=_("This is automatically set"))
    
    def __str__(self):
        return self.contact.full_name
    
    def copyAddresses(self):
        """
        Copy the address so we know what the information was at time of order
        """
        shipaddress = self.contact.shipping_address
        billaddress = self.contact.billing_address
        self.shipStreet1 = shipaddress.street1
        self.shipStreet2 = shipaddress.street2
        self.shipCity = shipaddress.city
        self.shipState = shipaddress.state
        self.shipPostalCode = shipaddress.postalCode
        self.shipCountry = shipaddress.country
        self.billStreet1 = billaddress.street1
        self.billStreet2 = billaddress.street2
        self.billCity = billaddress.city
        self.billState = billaddress.state
        self.billPostalCode = billaddress.postalCode
        self.billCountry = billaddress.country
        
    def copyItems(self):
        pass
    
    #def _status(self):
    #    return(self.orderstatus_set.latest('timeStamp').status)
    #status = property(_status)        
    
    def removeAllItems(self):
        for item in self.orderitem_set.all():
            item.delete()
        self.save()
    
    def _CC(self):
        return(self.creditcarddetail_set.all()[0])
    CC = property(_CC)
    
    def _fullBillStreet(self, delim="<br/>"):
        if self.billStreet2:
            return (self.billStreet1 + delim + self.billStreet2)
        else:
            return (self.billStreet1)
    fullBillStreet = property(_fullBillStreet)
    
    def _fullShipStreet(self, delim="<br/>"):
        if self.shipStreet2:
            return (self.shipStreet1 + delim + self.shipStreet2)
        else:
            return (self.shipStreet1)
    fullShipStreet = property(_fullShipStreet)
    
    def save(self):
        self.copyAddresses()
        super(Order, self).save() # Call the "real" save() method.
    
    def invoice(self):
        return('<a href="/admin/print/invoice/%s/">View</a>' % self.id)
    invoice.allow_tags = True
    
    def packingslip(self):
        return('<a href="/admin/print/packingslip/%s/">View</a>' % self.id)
    packingslip.allow_tags = True
    
    def shippinglabel(self):
        return('<a href="/admin/print/shippinglabel/%s/">View</a>' % self.id)
    shippinglabel.allow_tags = True
    
    def _order_total(self):
        #Needed for the admin list display
        return (moneyfmt(self.total))
    order_total = property(_order_total)
    
    class Admin:
        fields = (
        (None, {'fields': ('contact','method','status', 'notes')}),
        (_('Shipping Method'), {'fields': ('shippingMethod', 'shippingDescription')}),
        (_('Shipping Address'), {'fields': ('shipStreet1','shipStreet2', 'shipCity','shipState', 'shipPostalCode','shipCountry',), 'classes': 'collapse'}),
        (_('Billing Address'), {'fields': ('billStreet1','billStreet2', 'billCity','billState', 'billPostalCode','billCountry',), 'classes': 'collapse'}),
        (_('Totals'), {'fields': ( 'sub_total','shippingCost', 'tax', 'total','timeStamp','payment',),}),       
        )
        list_display = ('contact', 'timeStamp', 'order_total','status', 'invoice', 'packingslip', 'shippinglabel')
        list_filter = ['timeStamp','contact']
        date_hierarchy = 'timeStamp'
    
    class Meta:
        verbose_name = _("Product Order")
        verbose_name_plural = _("Product Orders")
        
class OrderItem(models.Model):
    """
    A line item on an order.
    """
    order = models.ForeignKey(Order, edit_inline=models.TABULAR, num_in_admin=3)
    item = models.ForeignKey(SubItem)
    quantity = models.IntegerField(_("Quantity"), core=True)
    unitPrice = models.FloatField(_("Unit price"), max_digits=6,decimal_places=2)
    lineItemPrice = models.FloatField(_("Line item price"), max_digits=6,decimal_places=2)
    
    def __str__(self):
        return self.item.full_name
    
    class Meta:
        verbose_name = _("Order Line Item")
        verbose_name_plural = _("Order Line Items")

class OrderStatus(models.Model):
    """
    An order will have multiple statuses as it moves its way through processing.
    """
    order = models.ForeignKey(Order, edit_inline=models.STACKED, num_in_admin=1)
    status = models.CharField(_("Status"), maxlength=20, choices=ORDER_STATUS, core=True, blank=True)
    notes = models.CharField(_("Notes"), maxlength=100, blank=True)
    timeStamp = models.DateTimeField(_("Time Stamp"))
    
    def __str__(self):
        return self.status

    def save(self):
        super(OrderStatus, self).save()
        self.order.status = self.status
        self.order.save()
    
    class Meta:
        verbose_name = _("Order Status")
        verbose_name_plural = _("Order statuses")        