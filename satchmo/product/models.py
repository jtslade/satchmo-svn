from django.db import models
from sets import Set

# Create your models here.

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
    featured = models.BooleanField("Featured Item", default=False, help_text="Featured items will show on the front page")
    optionGroups = models.ManyToManyField(OptionGroup, filter_interface=True, blank=True)
    price = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Base price for this item")
    weight = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True, )
    length = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    width = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    create_subs = models.BooleanField("Create Sub Items", default=False, help_text ="This will erase any existing sub-items!")
    relatedItems = models.ManyToManyField('self', blank=True, null=True, related_name='related')
    alsoPurchased = models.ManyToManyField('self', blank=True, null=True, related_name='previouslyPurchased')
    
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
            sub = Sub_Item(item=self, items_in_stock='0', price_change='0')
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
        (None, {'fields': ('category','verbose_name','short_name','description','active','featured','price',)}),
        ('Item Dimensions', {'fields': (('length', 'width','height',),'weight'), 'classes': 'collapse'}),
        ('Options', {'fields': ('optionGroups','create_subs',),}), 
        ('Related Products', {'fields':('relatedItems','alsoPurchased'),'classes':'collapse'}),            
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
        if self.price_change > 0:
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
