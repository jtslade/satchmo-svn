from django import newforms as forms
from models import Product, Price
import logging

log = logging.getLogger('product.forms')

class InventoryForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        products = kwargs.pop('products', None)
        
        super(InventoryForm, self).__init__(*args, **kwargs)
        
        if not products:
            products = Product.objects.all().order_by('slug')
            
        for product in products:
            kw = { 
            'label' : product.slug,
            'help_text' : product.name,
            'initial' : product.items_in_stock }
            
            qty = forms.IntegerField(**kw)
            self.fields['qty__%s' % product.slug] = qty
            qty.slug = product.slug
            qty.product_id = product.id
            
            kw['initial'] = product.unit_price
            kw['required'] = False
            price = forms.DecimalField(**kw)
            price.slug = product.slug
            price.product_id = product.id
            self.fields['price__%s' % product.slug] = price
            
    def save(self, request):
        self.full_clean()
        for name, value in self.cleaned_data.items():
            opt, key = name.split('__')
            
            prod = Product.objects.get(slug__exact=key)
            if opt=='qty':
                if value != prod.items_in_stock:
                    request.user.message_set.create(message='Updated %s stock to %s' % (key, value))
                    log.debug('Saving new qty=%i for %s' % (value, key))
                    prod.items_in_stock = value
                    prod.save()
                
            elif opt=='price':
                if value != prod.unit_price:
                    request.user.message_set.create(message='Updated %s unit price to %s' % (key, value))
                    log.debug('Saving new price %s for %s' % (value, key))
                    try:
                        price = Price.objects.get(product=prod, quantity=1)
                    except Price.DoesNotExist:
                        price = Price(product=prod, quantity=1)
                        
                    price.price = value
                    price.save()
        
