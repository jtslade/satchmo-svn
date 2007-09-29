from django import newforms as forms
from django.core.management.base import CommandError
from django.http import HttpResponse
from models import Product, Price
import logging
import time

log = logging.getLogger('product.forms')

export_choices = (
    ('json', 'JSON'),
    ('yaml', 'YAML'),
    ('xml', 'XML')
    )

class ProductExportForm(forms.Form):    
    format = forms.ChoiceField(label=_('export format'), widget=forms.Select(), choices=export_choices, required=True)
    
    def __init__(self, *args, **kwargs):
        products = kwargs.pop('products', None)
        
        super(ProductExportForm, self).__init__(*args, **kwargs)
        
        if not products:
            products = Product.objects.all().order_by('slug')
            
        for product in products:
            subtypes = product.get_subtypes()
            expclasses = ('export', ) + subtypes
            extclasses = " ".join(expclasses)

            kw = { 
            'label' : product.slug,
            'help_text' : product.name,
            'initial' : False,
            'required' : False,
            'widget' : forms.CheckboxInput(attrs={'class': extclasses}) }
            
            chk = forms.BooleanField(**kw)
            chk.slug = product.slug
            chk.product_id = product.id
            chk.subtypes = " ".join(subtypes)            
            self.fields['export__%s' % product.slug] = chk
            
    def export(self, request):
        self.full_clean()
        format = 'yaml'
        selected = []
        
        for name, value in self.cleaned_data.items():
            if name == 'format':
                format == value
                continue
                
            opt, key = name.split('__')
            
            if opt=='export':
                if value:
                    selected.append(key)
                        
        from django.core import serializers

        try:
            serializers.get_serializer(format)
        except KeyError:
            raise CommandError("Unknown serialization format: %s" % format)

        objects = []
        for slug in selected:
            product = Product.objects.get(slug=slug)
            objects.append(product)
            for subtype in product.get_subtypes():
                objects.append(getattr(product,subtype.lower()))

        try:
            raw = serializers.serialize(format, objects, indent=False)
        except Exception, e:
            raise CommandError("Unable to serialize database: %s" % e)
            
        response = HttpResponse(mimetype="text/" + format, content=raw)
        response['Content-Disposition'] = 'attachment; filename="products-%s.%s"' % ((time.strftime('%Y%m%d-%H%M'), format))
        return response

class InventoryForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        products = kwargs.pop('products', None)

        super(InventoryForm, self).__init__(*args, **kwargs)

        if not products:
            products = Product.objects.all().order_by('slug')

        for product in products:
            subtypes = product.get_subtypes()
            qtyclasses = ('text', 'qty') + subtypes
            qtyclasses = " ".join(qtyclasses)

            kw = { 
            'label' : product.slug,
            'help_text' : product.name,
            'initial' : False,
            'widget' : forms.TextInput(attrs={'class': qtyclasses}) }

            qty = forms.IntegerField(**kw)
            self.fields['qty__%s' % product.slug] = qty
            qty.slug = product.slug
            qty.product_id = product.id
            qty.subtypes = " ".join(subtypes)

            kw['initial'] = product.unit_price
            kw['required'] = False
            kw['widget'] = forms.TextInput(attrs={'class': "text price"})
            price = forms.DecimalField(**kw)
            price.slug = product.slug
            self.fields['price__%s' % product.slug] = price

            kw['initial'] = product.active
            kw['widget'] = forms.CheckboxInput(attrs={'class': "checkbox active"})
            active = forms.BooleanField(**kw)
            active.slug = product.slug
            self.fields['active__%s' % product.slug] = active

            kw['initial'] = product.featured
            kw['widget'] = forms.CheckboxInput(attrs={'class': "checkbox featured"})
            featured = forms.BooleanField(**kw)
            featured.slug = product.slug
            self.fields['featured__%s' % product.slug] = featured

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

            elif opt=="active":
                if value != prod.active:
                    if value:
                        note = "Activated %s"
                    else:
                        note = "Deactivated %s"
                    request.user.message_set.create(message=note % (key))

                    prod.active = value
                    prod.save()

            elif opt=="featured":
                if value != prod.featured:
                    if value:
                        note = "%s is now featured"
                    else:
                        note = "%s is no longer featured"
                    request.user.message_set.create(message=note % (key))

                    prod.featured = value
                    prod.save()
