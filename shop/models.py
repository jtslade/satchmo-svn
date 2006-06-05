from django.db import models
from django.core import validators
from sets import Set

class Customer(models.Model):
    first_name = models.CharField(maxlength=30, core=True)
    last_name = models.CharField(maxlength=30, core=True)
    dob = models.DateField(blank=True, null=True)
    phone = models.CharField(maxlength=96,blank=True)
    fax=models.PhoneNumberField( blank=True)
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
       return self.description
       
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
        pass
        

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

class Category(models.Model):
        name = models.CharField(core=True, maxlength=200)
        slug = models.SlugField(prepopulate_from=('name',),help_text="Used for URLs",)
        parent = models.ForeignKey('self', blank=True, null=True, related_name='child')
        description = models.TextField(blank=True,help_text="Optional")
        
        class Admin:
                list_display = ('name', '_parents_repr')
        
        def __str__(self):
                p_list = self._recurse_for_parents(self)
                p_list.append(self.name)
                return self.get_separator().join(p_list)
        
        def get_absolute_url(self):
                if self.parent_id:
                        return "/category/%s/%s/" % (self.parent.slug, self.slug)
                else:
                        return "/category/%s/" % (self.slug)
        
        def _recurse_for_parents(self, cat_obj):
                p_list = []
                if cat_obj.parent_id:
                        p = cat_obj.parent
                        p_list.append(p.name)
                        more = self._recurse_for_parents(p)
                        p_list.extend(more)
                if cat_obj == self and p_list:
                        p_list.reverse()
                return p_list
                
        def get_separator(self):
                return ' :: '
        
        def _parents_repr(self):
                p_list = self._recurse_for_parents(self)
                return self.get_separator().join(p_list)
        _parents_repr.short_description = "Category parents"
        
        def save(self):
                p_list = self._recurse_for_parents(self)
                if self.name in p_list:
                        raise validators.ValidationError("You must not save a category in itself!")
                super(Category, self).save()
        
        class Meta:
            verbose_name = "Category"
            verbose_name_plural = "Categories"

class SupplierOrderStatus(models.Model):
    order = models.ForeignKey(SupplierOrder, edit_inline=models.STACKED, num_in_admin=1)
    status = models.CharField(maxlength=20, choices=SUPPLIERORDER_STATUS, core=True, blank=True)
    notes = models.CharField(maxlength=100, blank=True)
    date = models.DateField(blank=True)
    
    def __str__(self):
        return str(self.date)

class OptionGroup(models.Model):
    name = models.CharField("Name of Option Group",maxlength = 50, core=True, help_text='This will be the text displayed on the product page',)
    description = models.CharField("Detailed Description",maxlength = 100, blank=True, help_text='Further description of this group i.e. shirt size vs shoe size',)
    sort_order = models.IntegerField(help_text="The order they will be displayed on the screen")
    
    def __str__(self):
        return self.name
    
    class Admin:
        list_display = ('name', 'description')
        
class Item(models.Model):
    category = models.ForeignKey(Category)
    verbose_name = models.CharField("Full Name", maxlength=255)
    short_name = models.SlugField("Slug Name", prepopulate_from=("verbose_name",), help_text="This is a short, descriptive name of the shirt that will be used in the URL link to this item")
    description = models.TextField("Description of product", help_text="This field can contain HTML and should be a few paragraphs explaining the background of the product, and anything that would help the potential customer make their purchase.")
    active = models.BooleanField("Is product active?", default=True, help_text="This will determine whether or not this product will appear on the site")
    optionGroups = models.ManyToManyField(OptionGroup, filter_interface=True, blank=True)
    price = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Base price for this item")
    weight = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True, )
    length = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    width = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    create_subs = models.BooleanField("Create Sub Items", default=False, help_text ="This will erase any existing sub-items!")
    
    def __str__(self):
        return self.short_name 
    
    def _cross_list(self, sequences):
        """
        Code taken from the Python cookbook v.2 (19.9 - Looping through the cross-product of multiple iterators)
        This is used to create all the sub items associated with an item
        """
        result =[[]]
        for seq in sequences:
            result = [sublist+[item] for sublist in result for item in seq]
        return result
    
    def create_subitems(self):
        """
        Get a list of all the optiongroups applied to this object
        Create all combinations of the options and create subitems
        """
        sublist = []
        masterlist = []
        #Create a list of all the options & create all combos of the options
        for opt in self.optionGroups.all():
            for value in opt.optionitem_set.all():
                sublist.append(value)
            masterlist.append(sublist)
            sublist = []
        combinedlist = self._cross_list(masterlist)
        #Create new sub_items for each combo
        for options in combinedlist:
            sub = Sub_Item(item=self, items_in_stock=0, price_change=0)
            sub.save()
            for option in options:
                sub.options.add(option)
                sub.save()
        return(True)
    
    def get_sub_item(self, optionSet):
        for sub in self.sub_item_set.all():
            if sub.option_values == optionSet:
                return(sub)
        return(None)
        
    
    def save(self):
        '''
        Right now this only works if you save the suboptions, then go back and choose to create the sub_items
        '''
        super(Item, self).save()
        if self.create_subs:
            self.create_subitems()
            self.create_subs = False
        super(Item, self).save()
    
    class Admin: 
        list_display = ('verbose_name', 'active')
        fields = (
        (None, {'fields': ('category','verbose_name','short_name','description','active','price',)}),
        ('Item Dimensions', {'fields': (('length', 'width','height',),'weight'), 'classes': 'collapse'}),
        ('Options', {'fields': ('optionGroups','create_subs',),}),       
        )
        list_filter = ('category',)
        
    class Meta:
        verbose_name = "Master Product"
        
class OptionItem(models.Model):
    optionGroup = models.ForeignKey(OptionGroup, edit_inline=models.TABULAR, num_in_admin=5)
    name = models.CharField("Display value", maxlength = 50, core=True)
    value = models.CharField("Stored value", prepopulate_from=("name",), maxlength = 50)
    displayOrder = models.IntegerField("Display Order")
  
    def __str__(self):
        return self.name
        

class Sub_Item(models.Model):
    item = models.ForeignKey(Item)
    items_in_stock = models.IntegerField("Number in stock", core=True)
    price_change = models.FloatField("Price Change", null=True, blank=True, help_text="This is the price differential for this product", max_digits=4, decimal_places=2)
    weight = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    length = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    width = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    options = models.ManyToManyField(OptionItem, filter_interface=True)
    
    def _get_optionName(self):
        "Returns the options in a human readable form"
        output = self.item.verbose_name + " ( "
        numProcessed = 0
        for option in self.options.all():
            numProcessed += 1
            if numProcessed == self.options.count():
                output += option.name
            else:
                output += option.name + "/"
        output += " )"
        return output
    full_name = property(_get_optionName)
    
    def _get_fullPrice(self):
        if self.price_change:
            return(self.item.price + self.price_change)
        else:
            return(self.item.price)
    unit_price = property(_get_fullPrice)
    
    def _get_optionValues(self):
        """
        Return a set of all the valid options for this sub item.  A set makes sure we don't have to worry about ordering
        """
        output = Set()
        for option in self.options.all():
            output.add(option.value)
        return(output)
    option_values = property(_get_optionValues)
    
    def _check_optionParents(self):
        groupList = []
        for option in self.options.all():
            if option.optionGroup.id in groupList:
                return(True)
            else:
                groupList.append(option.optionGroup.id)
        return(False)
            
    
    def in_stock(self):
        if self.items_in_stock > 0:
            return True
        else:
            return False;

    def __str__(self):
        return self.full_name
    
    def isValidOption(self, field_data, all_data):
        raise validators.ValidationError, "Two options from the same option group can not be applied to an item."
    
    #def save(self):
    #    super(Sub_Item, self).save()
    #    if self._check_optionParents():
    #        super(Sub_Item, self).delete()
    #        raise validators.ValidationError, "Two options from the same option group can not be applied to an item."
    #    else:
    #        super(Sub_Item, self).save()
    
    class Admin:
        list_display = ('full_name', 'unit_price', 'items_in_stock')
        list_filter = ('item',)
        fields = (
        (None, {'fields': ('item','items_in_stock','price_change',)}),
        ('Item Dimensions', {'fields': (('length', 'width','height',),'weight'), 'classes': 'collapse'}),
        ('Options', {'fields': ('options',),}),       
        )

    class Meta:
        verbose_name = "Individual Product"

    

ORDER_CHOICES = (
    ('Online', 'Online'),
    ('In Person', 'In Person'),
    ('Show', 'Show'),
)

ORDER_STATUS = (
    ('Pending', 'Pending'),
    ('Shipped', 'Shipped'),
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
    method = models.CharField(choices=ORDER_CHOICES, maxlength=50)
    shippingCost = models.FloatField(max_digits=6, decimal_places=2)
    tax = models.FloatField(max_digits=6, decimal_places=2)
    date = models.DateTimeField()
    
    def __str__(self):
        return self.customer.first_name
    
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
        
        
    def save(self):
        self.copyAddresses()
        super(Order, self).save() # Call the "real" save() method.
        
    class Admin:
        fields = (
        (None, {'fields': ('customer','method',)}),
        ('Shipping Information', {'fields': ('shipStreet1','shipStreet2', 'shipCity','shipState', 'shipZip_code','shipCountry',), 'classes': 'collapse'}),
        ('Billing Information', {'fields': ('billStreet1','billStreet2', 'billCity','billState', 'billZip_code','billCountry',), 'classes': 'collapse'}),
        ('Totals', {'fields': ( 'shippingCost', 'tax','total','date',),}),       
        )
        list_display = ('customer', 'date', 'total')
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
        return self.description

class OrderStatus(models.Model):
    order = models.ForeignKey(Order, edit_inline=models.STACKED, num_in_admin=1)
    status = models.CharField(maxlength=20, choices=ORDER_STATUS, core=True, blank=True)
    notes = models.CharField(maxlength=100, blank=True)
    date = models.DateField(blank=True)
    
    def __str__(self):
        return self.status
 
