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
    name = models.CharField(_("Name"), max_length=50, core=True)
    type = models.CharField(_("Type"), max_length=30,
        choices=ORGANIZATION_CHOICES)
    role = models.CharField(_("Role"), max_length=30,
        choices=ORGANIZATION_ROLE_CHOICES)
    create_date = models.DateField(_("Creation Date"))
    notes = models.TextField(_("Notes"), max_length=200, blank=True, null=True)

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
    first_name = models.CharField(_("First name"), max_length=30, core=True)
    last_name = models.CharField(_("Last name"), max_length=30, core=True)
    user = models.ForeignKey(User, unique=True, blank=True, null=True,
        edit_inline=models.TABULAR, num_in_admin=1, min_num_in_admin=1,
        max_num_in_admin=1, num_extra_on_change=0)
    role = models.CharField(_("Role"), max_length=20, blank=True, null=True,
        choices=CONTACT_CHOICES)
    organization = models.ForeignKey(Organization, blank=True, null=True)
    dob = models.DateField(_("Date of birth"), blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True)
    notes = models.TextField(_("Notes"), max_length=500, blank=True)
    create_date = models.DateField(_("Creation date"))
    newsletter = models.BooleanField(_("Newsletter"), null=True, default=False);

    @classmethod
    def from_request(cls, request, create=False):
        """Get the contact from the session, else lookup using the logged-in user.
        Optionally create an an unsaved new contact if `create` is true.
        
        Returns:
        - Contact object or None
        """
        contact = None
        if request.session.get('custID'):
            try:
                contact = cls.objects.get(id=request.session['custID'])
            except Contact.DoesNotExist:
                pass

        if contact is None and request.user.is_authenticated():
            try:
                contact = cls.objects.get(user=request.user.id)
                request.session['custID'] = contact
            except Contact.DoesNotExist:
                pass
        else:
            # can't create if no authenticated user
            create = False
                
        if contact is None and create:
            contact = Contact(user=request.user)
            
        return contact

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
    type = models.CharField(_("Type"), max_length=30,choices=INTERACTION_CHOICES)
    date_time = models.DateTimeField(_("Date and Time"), core=True)
    description = models.TextField(_("Description"), max_length=200)

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
        max_length=20, blank=True)
    phone = models.CharField(_("Phone Number"), blank=True, max_length=12,
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
    description = models.CharField(_("Description"), max_length=20, blank=True,
        help_text=_('Description of address - Home, Office, Warehouse, etc.',))
    street1 = models.CharField(_("Street"), core=True, max_length=50)
    street2 = models.CharField(_("Street"), max_length=50, blank=True)
    city = models.CharField(_("City"), max_length=50)
    state = models.CharField(_("State"), max_length=10, blank=True)
    postal_code = models.CharField(_("Zip Code"), max_length=10)
    country = models.CharField(_("Country"), max_length=50, blank=True)
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
    ship_street1 = models.CharField(_("Street"), max_length=50, blank=True)
    ship_street2 = models.CharField(_("Street"), max_length=50, blank=True)
    ship_city = models.CharField(_("City"), max_length=50, blank=True)
    ship_state = models.CharField(_("State"), max_length=10, blank=True)
    ship_postal_code = models.CharField(_("Zip Code"), max_length=10, blank=True)
    ship_country = models.CharField(_("Country"), max_length=50, blank=True)
    bill_street1 = models.CharField(_("Street"), max_length=50, blank=True)
    bill_street2 = models.CharField(_("Street"), max_length=50, blank=True)
    bill_city = models.CharField(_("City"), max_length=50, blank=True)
    bill_state = models.CharField(_("State"), max_length=10, blank=True)
    bill_postal_code = models.CharField(_("Zip Code"), max_length=10, blank=True)
    bill_country = models.CharField(_("Country"), max_length=50, blank=True)
    notes = models.TextField(_("Notes"), max_length=100, blank=True, null=True)
    sub_total = models.DecimalField(_("Subtotal"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(_("Total"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    discount = models.DecimalField(_("Discount"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    payment= models.CharField(_("Payment"),
        choices=PAYMENT_CHOICES, max_length=25, blank=True)
    method = models.CharField(_("Payment method"),
        choices=ORDER_CHOICES, max_length=50, blank=True)
    shipping_description = models.CharField(_("Shipping Description"),
        max_length=50, blank=True, null=True)
    shipping_method = models.CharField(_("Shipping Method"),
        max_length=50, blank=True, null=True)
    shipping_model = models.CharField(_("Shipping Models"),
        choices=activeShippingModules, max_length=30, blank=True, null=True)
    shipping_cost = models.DecimalField(_("Shipping Cost"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    tax = models.DecimalField(_("Tax"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    timestamp = models.DateTimeField(_("Timestamp"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=ORDER_STATUS,
        core=True, blank=True, help_text=_("This is set automatically."))

    def __unicode__(self):
        return self.contact.full_name

    def copy_addresses(self):
        """
        Copy the addresses so we know what the information was at time of order.
        """
        shipaddress = self.contact.shipping_address
        billaddress = self.contact.billing_address
        self.ship_street1 = shipaddress.street1
        self.ship_street2 = shipaddress.street2
        self.ship_city = shipaddress.city
        self.ship_state = shipaddress.state
        self.ship_postal_code = shipaddress.postal_code
        self.ship_country = shipaddress.country
        self.bill_street1 = billaddress.street1
        self.bill_street2 = billaddress.street2
        self.bill_city = billaddress.city
        self.bill_state = billaddress.state
        self.bill_postal_code = billaddress.postal_code
        self.bill_country = billaddress.country

    def remove_all_items(self):
        """Delete all items belonging to this order."""
        for item in self.orderitem_set.all():
            item.delete()
        self.save()

    def _credit_card(self):
        """Return the credit card associated with this order."""
        try:
            return self.creditcarddetail_set.get()
        except self.creditcarddetail_set.model.DoesNotExist:
            return None
    credit_card = property(_credit_card)

    def _full_bill_street(self, delim="<br/>"):
        """Return both billing street entries separated by delim."""
        if self.bill_street2:
            return self.bill_street1 + delim + self.bill_street2
        else:
            return self.bill_street1
    full_bill_street = property(_full_bill_street)

    def _full_ship_street(self, delim="<br/>"):
        """Return both shipping street entries separated by delim."""
        if self.ship_street2:
            return self.ship_street1 + delim + self.ship_street2
        else:
            return self.ship_street1
    full_ship_street = property(_full_ship_street)

    def save(self):
        """
        Copy addresses from contact. If the order has just been created, set
        the create_date.
        """
        if not self.id:
            self.timestamp = datetime.datetime.now()

        self.copy_addresses()
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
                ('shipping_method', 'shipping_description')}),
            (_('Shipping Address'), {'classes': 'collapse', 'fields':
                ('ship_street1', 'ship_street2', 'ship_city', 'ship_state',
                'ship_postal_code', 'ship_country')}),
            (_('Billing Address'), {'classes': 'collapse', 'fields':
                ('bill_street1', 'bill_street2', 'bill_city', 'bill_state',
                'bill_postal_code', 'bill_country')}),
            (_('Totals'), {'fields':
                ('sub_total', 'shipping_cost', 'tax', 'discount', 'total',
                'timestamp', 'payment')}))
        list_display = ('contact', 'timestamp', 'order_total', 'status',
            'invoice', 'packingslip', 'shippinglabel')
        list_filter = ['timestamp', 'contact']
        date_hierarchy = 'timestamp'

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
    unit_price = models.DecimalField(_("Unit price"),
        max_digits=6, decimal_places=2)
    line_item_price = models.DecimalField(_("Line item price"),
        max_digits=6, decimal_places=2)

    def __unicode__(self):
        return self.product.name

    def _get_category(self):
        return(self.product.get_category)
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
        max_length=20, choices=ORDER_STATUS, core=True, blank=True)
    notes = models.CharField(_("Notes"), max_length=100, blank=True)
    timestamp = models.DateTimeField(_("Timestamp"))

    def __unicode__(self):
        return self.status

    def save(self):
        super(OrderStatus, self).save()
        self.order.status = self.status
        self.order.save()

    class Meta:
        verbose_name = _("Order Status")
        verbose_name_plural = _("Order Statuses")


