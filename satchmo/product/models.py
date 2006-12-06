"""
Base model used for products.  Stores hierarchical categories
as well as individual product level information which includes
options.
"""

from django.db import models
from django.core import validators
from sets import Set
from satchmo.thumbnail.field import ImageWithThumbnailField
from django.conf import settings
import os

# Create your models here.

class Category(models.Model):
    """
    Basic hierarchical category model for storing products
    """
    name = models.CharField(core=True, maxlength=200)
    slug = models.SlugField(prepopulate_from=('name',),help_text="Used for URLs",)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='child')
    description = models.TextField(blank=True,help_text="Optional")
        
    def _recurse_for_parents_slug(self, cat_obj):
        #This is used for the urls
        p_list = []
        if cat_obj.parent_id:
            p = cat_obj.parent
            p_list.append(p.slug)
            more = self._recurse_for_parents_slug(p)
            p_list.extend(more)
        if cat_obj == self and p_list:
            p_list.reverse()
        return p_list

    def get_absolute_url(self):
        p_list = self._recurse_for_parents_slug(self)
        p_list.append(self.slug)
        baseurl = settings.SHOP_BASE + "/category/"
        return baseurl + "/".join(p_list)        
                
    def _recurse_for_parents_name(self, cat_obj):
        #This is used for the visual display & save validation
        p_list = []
        if cat_obj.parent_id:
            p = cat_obj.parent
            p_list.append(p.name)
            more = self._recurse_for_parents_name(p)
            p_list.extend(more)
        if cat_obj == self and p_list:
            p_list.reverse()
        return p_list
                
    def get_separator(self):
        return ' :: '
        
    def _parents_repr(self):
        p_list = self._recurse_for_parents_name(self)
        return self.get_separator().join(p_list)
    _parents_repr.short_description = "Category parents"
    
    def _recurse_for_parents_name_url(self, cat_obj):
        #Get all the absolute urls and names (for use in site navigation)
        p_list = []
        url_list = []
        if cat_obj.parent_id:
            p = cat_obj.parent
            p_list.append(p.name)
            url_list.append(p.get_absolute_url())
            more, url = self._recurse_for_parents_name_url(p)
            p_list.extend(more)
            url_list.extend(url)
        if cat_obj == self and p_list:
            p_list.reverse()
            url_list.reverse()
        return p_list, url_list

    def get_url_name(self):
        #Get a list of the url to display and the actual urls
        p_list, url_list = self._recurse_for_parents_name_url(self)
        p_list.append(self.name)
        url_list.append(self.get_absolute_url())
        return zip(p_list, url_list)
    
    def __str__(self):
        p_list = self._recurse_for_parents_name(self)
        p_list.append(self.name)
        return self.get_separator().join(p_list)
        
    def save(self):
        p_list = self._recurse_for_parents_name(self)
        if self.name in p_list:
            raise validators.ValidationError("You must not save a category in itself!")
        super(Category, self).save()
        
    def _flatten(self, L):
        """
        Taken from a python newsgroup post
        """
        if type(L) != type([]): return [L]
        if L == []: return L
        return self._flatten(L[0]) + self._flatten(L[1:])
            
    def _recurse_for_children(self, node):
        children = []
        children.append(node)
        for child in node.child.all():
            children_list = self._recurse_for_children(child)
            children.append(children_list)
        return(children)

    def get_all_children(self):
        """
        Gets a list of all of the children categories.
        """
        children_list = self._recurse_for_children(self)
        flat_list = self._flatten(children_list[1:])
        return(flat_list)
    
    class Admin:
        list_display = ('name', '_parents_repr')
        ordering = ['name']
        
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

class OptionGroup(models.Model):
    """
    A set of options that can be applied to an item.
    Examples - Size, Color, Shape, etc
    """
    name = models.CharField("Name of Option Group",maxlength = 50, core=True, help_text='This will be the text displayed on the product page',)
    description = models.CharField("Detailed Description",maxlength = 100, blank=True, help_text='Further description of this group i.e. shirt size vs shoe size',)
    sort_order = models.IntegerField(help_text="The order they will be displayed on the screen")
    
    def __str__(self):
        if self.description:
            return ("%s - %s" % (self.name, self.description))
        else:
            return self.name
    
    class Admin:
        pass
        
    class Meta:
        ordering = ['sort_order']
        
class Item(models.Model):
    """
    The basic product being sold in the store.  This is what the customer sees.
    """
    category = models.ManyToManyField(Category, filter_interface=True)
    verbose_name = models.CharField("Full Name", maxlength=255)
    short_name = models.SlugField("Slug Name", prepopulate_from=("verbose_name",), unique=True, help_text="This is a short, descriptive name of the shirt that will be used in the URL link to this item")
    description = models.TextField("Description of product", help_text="This field can contain HTML and should be a few paragraphs explaining the background of the product, and anything that would help the potential customer make their purchase.")
    date_added = models.DateField(null=True, blank=True, auto_now_add=True)
    active = models.BooleanField("Is product active?", default=True, help_text="This will determine whether or not this product will appear on the site")
    featured = models.BooleanField("Featured Item", default=False, help_text="Featured items will show on the front page")
    option_group = models.ManyToManyField(OptionGroup, filter_interface=True, blank=True)
    price = models.FloatField(max_digits=6, decimal_places=2, help_text="Base price for this item")
    weight = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True, )
    length = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    width = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    create_subs = models.BooleanField("Create Sub Items", default=False, help_text ="Create new sub-items")
    relatedItems = models.ManyToManyField('self', blank=True, null=True, related_name='related')
    alsoPurchased = models.ManyToManyField('self', blank=True, null=True, related_name='previouslyPurchased')
        
    def __str__(self):
        return self.short_name 
    
    def _get_mainImage(self):
        if self.itemimage_set.count() > 0:
            return(self.itemimage_set.order_by('sort')[0])
        else:
            return(False)
    main_image = property(_get_mainImage)
    
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
        for opt in self.option_group.all():
            for value in opt.optionitem_set.all():
                sublist.append(value)
            masterlist.append(sublist)
            sublist = []
        combinedlist = self._cross_list(masterlist)
        #Create new sub_items for each combo
        for options in combinedlist:
            price_delta = 0
            sub = SubItem(item=self, items_in_stock=0)
            sub.save()
            s1 = Set()
            for option in options:
                sub.options.add(option)
                optionValue = "%s-%s" % (option.optionGroup.id, option.value)
                s1.add(optionValue)
                sub.save()
            #If the option already exists, lets make sure there are no dupes
            #TODO: Check before we create the item
            if self.get_sub_item_count(s1) > 1:              
                sub.delete()
        return(True)
    
    def get_sub_item(self, optionSet):
        for sub in self.subitem_set.all():
            if sub.option_values == optionSet:
                return(sub)
        return(None)
    
    def get_sub_item_count(self, optionSet):
        count = 0
        for sub in self.subitem_set.all():
            if sub.option_values == optionSet:
                count+=1
        return count
    
    def save(self):
        '''
        Right now this only works if you save the suboptions, then go back and choose to create the subitems
        '''
        #super(Item,self).save()
        if self.create_subs:
            self.create_subitems()
            self.create_subs = False
        super(Item, self).save()
    
    def get_absolute_url(self):
        return "%s/product/%s" % (settings.SHOP_BASE,self.short_name)

    
    class Admin: 
        list_display = ('verbose_name', 'active')
        fields = (
        (None, {'fields': ('category','verbose_name','short_name','description','date_added','active','featured','price',)}),
        ('Item Dimensions', {'fields': (('length', 'width','height',),'weight'), 'classes': 'collapse'}),
        ('Options', {'fields': ('option_group','create_subs',),}), 
        ('Related Products', {'fields':('relatedItems','alsoPurchased'),'classes':'collapse'}),            
        )
        list_filter = ('category',)
        
    class Meta:
        verbose_name = "Master Product"
        
class ItemImage(models.Model):
    """
    A picture of an item.  Can have many pictures associated with an item.
    Thumbnails are automatically created.
    """
    item = models.ForeignKey(Item, edit_inline=models.TABULAR, num_in_admin=3)
    picture = ImageWithThumbnailField(upload_to="./images") #Media root is automatically appended
    caption = models.CharField("Optional caption",maxlength=100,null=True, blank=True)
    sort = models.IntegerField("Sort Order", help_text="Leave blank to delete", core=True)
    
    def __str__(self):
        return "Picture of %s" % self.item.short_name
        
    class Meta:
        ordering = ['sort']
        
class OptionItem(models.Model):
    """
    These are the actual items in and OptionGroup.  If the OptionGroup is Size, then an OptionItem
    would be Small.
    """
    optionGroup = models.ForeignKey(OptionGroup, edit_inline=models.TABULAR, num_in_admin=5)
    name = models.CharField("Display value", maxlength = 50, core=True)
    value = models.CharField("Stored value", prepopulate_from=("name",), maxlength = 50)
    price_change = models.FloatField("Price Change", null=True, blank=True, 
                                    help_text="This is the price differential for this option", max_digits=4, decimal_places=2)
    displayOrder = models.IntegerField("Display Order")
  
    def __str__(self):
        return self.name
        
    class Meta:
        ordering = ['displayOrder']
        
class SubItem(models.Model):
    """
    The unique inventoriable item.  For instance, if a shirt has a size and color, then
    only 1 SubItem would have Size=Small and Color=Black
    """
    item = models.ForeignKey(Item)
    items_in_stock = models.IntegerField("Number in stock", core=True)
    weight = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    length = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    width = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.FloatField(max_digits=6, decimal_places=2, null=True, blank=True)
    options = models.ManyToManyField(OptionItem, filter_interface=True, null=True, blank=True)
    
    def _get_optionName(self):
        "Returns the options in a human readable form"
        if self.options.count() == 0:
            return self.item.verbose_name
        output = self.item.verbose_name + " ( "
        numProcessed = 0
        for option in self.options.order_by('displayOrder'):
            numProcessed += 1
            if numProcessed == self.options.count():
                output += option.name
            else:
                output += option.name + "/"
        output += " )"
        return output
    full_name = property(_get_optionName)
    
    def _get_fullPrice(self):
        price_delta = 0
        for option in self.options.all():
            if option.price_change:
                price_delta += option.price_change
            return(self.item.price + price_delta)
    unit_price = property(_get_fullPrice)
    
    def _get_optionValues(self):
        """
        Return a set of all the valid options for this sub item.  A set makes sure we don't have to worry about ordering
        """
        output = Set()
        for option in self.options.all():
            outvalue = "%s-%s" % (option.optionGroup.id,option.value)
            output.add(outvalue)
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
        (None, {'fields': ('item','items_in_stock',)}),
        ('Item Dimensions', {'fields': (('length', 'width','height',),'weight'), 'classes': 'collapse'}),
        ('Options', {'fields': ('options',),}),       
        )

    class Meta:
        verbose_name = "Individual Product"
