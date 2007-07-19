"""
Stores customer, organization, and order information.
"""

import datetime
import sys
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from satchmo.product.models import Product
from satchmo.newsletter import SubscriptionManager
from satchmo.shop.templatetags.currency_filter import moneyfmt

activeShippingModules = []

#Load the shipping modules to populate the choices
#None is passed in, since all we need is the id
for module in settings.SHIPPING_MODULES:
    __import__(module)
    shipping_module = sys.modules[module]
    activeShippingModules.append((shipping_module.Calc(None, None).id,
        shipping_module.Calc(None, None).id))

CONTACT_CHOICES = (
    ('Customer', _('Customer')),
    ('Supplier', _('Supplier')),
    ('Distributor', _('Distributor')),
)

ORGANIZATION_CHOICES = (
    ('Company', _('Company')),
    ('Government', _('Government')),
    ('Non-profit', _('Non-profit')),
)

ORGANIZATION_ROLE_CHOICES = (
    ('Supplier', _('Supplier')),
    ('Distributor', _('Distributor')),
    ('Manufacturer', _('Manufacturer')),
)

class Organization(models.Model):
    """
    An organization can be a company, government or any kind of group.
    """
    name = models.CharField(_("Name"), maxlength=50, core=True)
    type = models.CharField(_("Type"), maxlength=30,
        choices=ORGANIZATION_CHOICES)
    role = models.CharField(_("Role"), maxlength=30,
        choices=ORGANIZATION_ROLE_CHOICES)
    create_date = models.DateField(_("Creation Date"))
    notes = models.TextField(_("Notes"), maxlength=200, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def save(self):
        """Ensure we have a create_date before saving the first time."""
        if not self.id:
            self.create_date = datetime.date.today()
        super(Organization, self).save()

    class Admin:
        list_filter = ['type', 'role']
        list_display = ['name', 'type', 'role']

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

class Contact(models.Model):
    """
    A customer, supplier or any individual that a store owner might interact
    with.
    """
    first_name = models.CharField(_("First Name"), maxlength=30, core=True)
    last_name = models.CharField(_("Last Name"), maxlength=30, core=True)
    user = models.ForeignKey(User, unique=True, blank=True, null=True,
        edit_inline=models.TABULAR, num_in_admin=1, min_num_in_admin=1,
        max_num_in_admin=1, num_extra_on_change=0)
    role = models.CharField(_("Role"), maxlength=20, blank=True, null=True,
        choices=CONTACT_CHOICES)
    organization = models.ForeignKey(Organization, blank=True, null=True)
    dob = models.DateField(_("Date of Birth"), blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True)
    notes = models.TextField(_("Notes"), maxlength=500, blank=True)
    create_date = models.DateField(_("Creation Date"))
    newsletter = models.BooleanField(_("Newsletter"), null=True, default=False);

    def _get_full_name(self):
        """Return the person's full name."""
        return u'%s %s' % (self.first_name, self.last_name)
    full_name = property(_get_full_name)

    def _shipping_address(self):
        """Return the default shipping address or None."""
        try:
            return self.addressbook_set.get(is_default_shipping=True)
        except AddressBook.DoesNotExist:
            return None
    shipping_address = property(_shipping_address)

    def _billing_address(self):
        """Return the default billing address or None."""
        try:
            return self.addressbook_set.get(is_default_billing=True)
        except AddressBook.DoesNotExist:
            return None
    billing_address = property(_billing_address)

    def _primary_phone(self):
        """Return the default phone number or None."""
        try:
            return self.phonenumber_set.get(primary=True)
        except PhoneNumber.DoesNotExist:
            return None
    primary_phone = property(_primary_phone)

    def __unicode__(self):
        return self.full_name

    def save(self):
        """Ensure we have a create_date before saving the first time."""
        if not self.id:
            self.create_date = datetime.date.today()
        super(Contact, self).save()
        SubscriptionManager().update_contact(self)

    class Admin:
        list_display = ('last_name', 'first_name', 'organization', 'role')
        list_filter = ['create_date', 'role', 'organization']
        ordering = ['last_name']

    class Meta:
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")

PHONE_CHOICES = (
    ('Work', _('Work')),
    ('Home', _('Home')),
    ('Fax', _('Fax')),
    ('Mobile', _('Mobile')),
)

INTERACTION_CHOICES = (
    ('Email', _('Email')),
    ('Phone', _('Phone')),
    ('In Person', _('In Person')),
)

class Interaction(models.Model):
    """
    A type of activity with the customer.  Useful to track emails, phone calls,
    or in-person interactions.
    """
    contact = models.ForeignKey(Contact)
    type = models.CharField(_("Type"), maxlength=30,choices=INTERACTION_CHOICES)
    date_time = models.DateTimeField(_("Date and Time"), core=True)
    description = models.TextField(_("Description"), maxlength=200)

    def __unicode__(self):
        return u'%s - %s' % (self.contact.full_name, self.type)

    class Admin:
        list_filter = ['type', 'date_time']

    class Meta:
        verbose_name = _("Interaction")
        verbose_name_plural = _("Interactions")

class PhoneNumber(models.Model):
    """
    Phone number associated with a contact.
    """
    contact = models.ForeignKey(Contact, edit_inline=models.TABULAR,
        num_in_admin=1)
    type = models.CharField(_("Description"), choices=PHONE_CHOICES,
        maxlength=20, blank=True)
    phone = models.CharField(_("Phone Number"), blank=True, maxlength=12,
        core=True)
    primary = models.BooleanField(_("Primary"), default=False)

    def __unicode__(self):
        return u'%s - %s' % (self.type, self.phone)

    def save(self):
        """
        If this number is the default, then make sure that it is the only
        primary phone number. If there is no existing default, then make
        this number the default.
        """
        existing_number = self.contact.primary_phone
        if existing_number:
            if self.primary:
                existing_number.primary = False
                super(PhoneNumber, existing_number).save()
        else:
            self.primary = True
        super(PhoneNumber, self).save()

    class Meta:
        ordering = ['-primary']
        verbose_name = _("Phone Number")
        verbose_name_plural = _("Phone Numbers")

class AddressBook(models.Model):
    """
    Address information associated with a contact.
    """
    contact = models.ForeignKey(Contact,
        edit_inline=models.STACKED, num_in_admin=1)
    description = models.CharField(_("Description"), maxlength=20, blank=True,
        help_text=_('Description of address - Home, Office, Warehouse, etc.',))
    street1 = models.CharField(_("Street"), core=True, maxlength=50)
    street2 = models.CharField(_("Street"), maxlength=50, blank=True)
    city = models.CharField(_("City"), maxlength=50)
    state = models.CharField(_("State"), maxlength=10)
    postalCode = models.CharField(_("Zip Code"), maxlength=10)
    country = models.CharField(_("Country"), maxlength=50, blank=True)
    is_default_shipping = models.BooleanField(_("Default Shipping Address"),
        default=False)
    is_default_billing = models.BooleanField(_("Default Billing Address"),
        default=False)

    def __unicode__(self):
       return u'%s - %s' % (self.contact.full_name, self.description)

    def save(self):
        """
        If this address is the default billing or shipping address, then
        remove the old address's default status. If there is no existing
        default, then make this address the default.
        """
        existing_billing = self.contact.billing_address
        if existing_billing:
            if self.is_default_billing:
                existing_billing.is_default_billing = False
                super(AddressBook, existing_billing).save()
        else:
            self.is_default_billing = True

        existing_shipping = self.contact.shipping_address
        if existing_shipping:
            if self.is_default_shipping:
                existing_shipping.is_default_shipping = False
                super(AddressBook, existing_shipping).save()
        else:
            self.is_default_shipping = True

        super(AddressBook, self).save()

    class Meta:
        verbose_name = _("Address Book")
        verbose_name_plural = _("Address Books")

ORDER_CHOICES = (
    ('Online', _('Online')),
    ('In Person', _('In Person')),
    ('Show', _('Show')),
)

ORDER_STATUS = (
    ('Temp', _('Temp')),
    ('Pending', _('Pending')),
    ('In Process', _('In Process')),
    ('Shipped', _('Shipped')),
)

PAYMENT_CHOICES = (
    ('Cash', _('Cash')),
    ('Credit Card', _('Credit Card')),
    ('Check', _('Check')),
)

class Order(models.Model):
    """
    Orders contain a copy of all the information at the time the order was
    placed.
    """
    contact = models.ForeignKey(Contact)
    shipStreet1=models.CharField(_("Street"), maxlength=50, blank=True)
    shipStreet2=models.CharField(_("Street"), maxlength=50, blank=True)
    shipCity=models.CharField(_("City"), maxlength=50, blank=True)
    shipState=models.CharField(_("State"), maxlength=10, blank=True)
    shipPostalCode=models.CharField(_("Zip Code"), maxlength=10, blank=True)
    shipCountry=models.CharField(_("Country"), maxlength=50, blank=True)
    billStreet1=models.CharField(_("Street"), maxlength=50, blank=True)
    billStreet2=models.CharField(_("Street"), maxlength=50, blank=True)
    billCity=models.CharField(_("City"), maxlength=50, blank=True)
    billState=models.CharField(_("State"), maxlength=10, blank=True)
    billPostalCode=models.CharField(_("Zip Code"), maxlength=10, blank=True)
    billCountry=models.CharField(_("Country"), maxlength=50, blank=True)
    notes = models.TextField(_("Notes"), maxlength=100, blank=True, null=True)
    sub_total = models.DecimalField(_("Sub total"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(_("Total"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    discount = models.DecimalField(_("Discount"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    payment= models.CharField(_("Payment"),
        choices=PAYMENT_CHOICES, maxlength=25, blank=True)
    method = models.CharField(_("Payment method"),
        choices=ORDER_CHOICES, maxlength=50, blank=True)
    shippingDescription = models.CharField(_("Shipping Description"),
        maxlength=50, blank=True, null=True)
    shippingMethod = models.CharField(_("Shipping Method"),
        maxlength=50, blank=True, null=True)
    shippingModel = models.CharField(_("Shipping Models"),
        choices=activeShippingModules, maxlength=30, blank=True, null=True)
    shippingCost = models.DecimalField(_("Shipping Cost"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    tax = models.DecimalField(_("Tax"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    timeStamp = models.DateTimeField(_("Time Stamp"), blank=True, null=True)
    status = models.CharField(_("Status"), maxlength=20, choices=ORDER_STATUS,
        core=True, blank=True, help_text=_("This is set automatically."))

    def __unicode__(self):
        return self.contact.full_name

    def copyAddresses(self):
        """
        Copy the address so we know what the information was at time of order.
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

    def removeAllItems(self):
        """Delete all items belonging to this order."""
        for item in self.orderitem_set.all():
            item.delete()
        self.save()

    def _CC(self):
        """Return the credit card associated with this order."""
        try:
            return self.creditcarddetail_set.get()
        except self.creditcarddetail_set.model.DoesNotExist:
            return None
    CC = property(_CC)

    def _fullBillStreet(self, delim="<br/>"):
        """Return both billing street entries separated by delim."""
        if self.billStreet2:
            return (self.billStreet1 + delim + self.billStreet2)
        else:
            return (self.billStreet1)
    fullBillStreet = property(_fullBillStreet)

    def _fullShipStreet(self, delim="<br/>"):
        """Return both shipping street entries separated by delim."""
        if self.shipStreet2:
            return (self.shipStreet1 + delim + self.shipStreet2)
        else:
            return (self.shipStreet1)
    fullShipStreet = property(_fullShipStreet)

    def save(self):
        """
        Copy addresses from contact. If the order has just been created, set
        the create_date.
        """
        if not self.id:
            self.timeStamp = datetime.datetime.now()

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
        return moneyfmt(self.total)
    order_total = property(_order_total)

    def order_success(self):
        """Run each item's order_success method."""
        for orderitem in self.orderitem_set.all():
            for subtype_name in orderitem.product.get_subtypes():
                subtype = getattr(orderitem.product, subtype_name.lower())
                success_method = getattr(subtype, 'order_success', None)
                if success_method:
                    success_method(self, orderitem)

    def validate(self, request):
        """
        Return whether the order is valid.
        Not guaranteed to be side-effect free.
        """
        valid = True
        for orderitem in self.orderitem_set.all():
            for subtype_name in orderitem.product.get_subtypes():
                subtype = getattr(orderitem.product, subtype_name.lower())
                validate_method = getattr(subtype, 'validate_order', None)
                if validate_method:
                    valid = valid and validate_method(request, self, orderitem)
        return valid

    class Admin:
        fields = (
            (None, {'fields': ('contact', 'method', 'status', 'notes')}),
            (_('Shipping Method'), {'fields':
                ('shippingMethod', 'shippingDescription')}),
            (_('Shipping Address'), {'classes': 'collapse', 'fields':
                ('shipStreet1', 'shipStreet2', 'shipCity', 'shipState',
                'shipPostalCode', 'shipCountry')}),
            (_('Billing Address'), {'classes': 'collapse', 'fields':
                ('billStreet1', 'billStreet2', 'billCity', 'billState',
                'billPostalCode', 'billCountry')}),
            (_('Totals'), {'fields':
                ('sub_total', 'shippingCost', 'tax', 'discount', 'total',
                'timeStamp', 'payment')}))
        list_display = ('contact', 'timeStamp', 'order_total', 'status',
            'invoice', 'packingslip', 'shippinglabel')
        list_filter = ['timeStamp', 'contact']
        date_hierarchy = 'timeStamp'

    class Meta:
        verbose_name = _("Product Order")
        verbose_name_plural = _("Product Orders")

class OrderItem(models.Model):
    """
    A line item on an order.
    """
    order = models.ForeignKey(Order, edit_inline=models.TABULAR, num_in_admin=3)
    product = models.ForeignKey(Product)
    quantity = models.IntegerField(_("Quantity"), core=True)
    unitPrice = models.DecimalField(_("Unit price"),
        max_digits=6, decimal_places=2)
    lineItemPrice = models.DecimalField(_("Line item price"),
        max_digits=6, decimal_places=2)

    def __unicode__(self):
        return self.product.full_name

    def _get_category(self):
        return(self.product.category.all()[0].name)
    category = property(_get_category)

    class Meta:
        verbose_name = _("Order Line Item")
        verbose_name_plural = _("Order Line Items")

class OrderStatus(models.Model):
    """
    An order will have multiple statuses as it moves its way through processing.
    """
    order = models.ForeignKey(Order, edit_inline=models.STACKED, num_in_admin=1)
    status = models.CharField(_("Status"),
        maxlength=20, choices=ORDER_STATUS, core=True, blank=True)
    notes = models.CharField(_("Notes"), maxlength=100, blank=True)
    timeStamp = models.DateTimeField(_("Time Stamp"))

    def __unicode__(self):
        return self.status

    def save(self):
        super(OrderStatus, self).save()
        self.order.status = self.status
        self.order.save()

    class Meta:
        verbose_name = _("Order Status")
        verbose_name_plural = _("Order statuses")

