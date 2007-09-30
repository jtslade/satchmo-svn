try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from django import newforms as forms
from django.core import serializers
from django.core.management.base import CommandError
from django.core.management.color import no_style
from django.http import HttpResponse
from models import Product, Price
import logging
import os
import time

log = logging.getLogger('product.forms')

def export_choices():
    fmts = serializers.get_serializer_formats()
    return zip(fmts,fmts)

class ProductExportForm(forms.Form):    
    
    def __init__(self, *args, **kwargs):
        products = kwargs.pop('products', None)
        
        super(ProductExportForm, self).__init__(*args, **kwargs)
        
        self.fields['format'] = forms.ChoiceField(label=_('export format'), choices=export_choices(), required=True)
        
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
            objects.extend(list(product.price_set.all()))
            objects.extend(list(product.productimage_set.all()))

        try:
            raw = serializers.serialize(format, objects, indent=False)
        except Exception, e:
            raise CommandError("Unable to serialize database: %s" % e)
            
        response = HttpResponse(mimetype="text/" + format, content=raw)
        response['Content-Disposition'] = 'attachment; filename="products-%s.%s"' % ((time.strftime('%Y%m%d-%H%M'), format))
        return response


class ProductImportForm(forms.Form):  
    
    def __init__(self, *args, **kwargs):        
        super(ProductImportForm, self).__init__(*args, **kwargs)
    
        self.fields['upload'] = forms.Field(label=_("File to import"), widget=forms.FileInput, required=False)

    def import_from(self, infile, maxsize=10000000):
        errors = []
        results = []
        
        filetype = infile['content-type']   
        filename = infile['filename']  
        raw = infile['content']
        
        # filelen = len(raw)
        # if filelen > maxsize:
        #     errors.append(_('Import too large, must be smaller than %i bytes.' % maxsize ))
        
        format = os.path.splitext(filename)[1]
        if format and format.startswith('.'):
            format = format[1:]
        if not format:
            errors.append(_('Could not parse format from filename: %s') % filename)
        
        elif not format in serializers.get_serializer_formats():
            errors.append(_('Unknown file format: %s') % format)
            
        if not errors:
            serializer = serializers.get_serializer(format)
            
            from django.db import connection, transaction
            
            transaction.commit_unless_managed()
            transaction.enter_transaction_management()
            transaction.managed(True)
        
            try:
                raw = StringIO(str(raw))
                objects = serializers.deserialize(format, raw)
                ct = 0
                models = set()
                for obj in objects:
                    obj.save()
                    models.add(obj.object.__class__)
                    ct += 1
                if ct>0:
                    style=no_style()
                    sequence_sql = connection.ops.sequence_reset_sql(style, models)
                    if sequence_sql:
                        cursor = connection.cursor()
                        for line in sequence_sql:
                            cursor.execute(line)
                    
                results.append(_('Added %i objects from %s') % (ct, filename));
                #label_found = True
            except Exception, e:
                #fixture.close()
                errors.append(_("Problem installing fixture '%s': %s\n") % (filename, str(e)))
                errors.append("Raw: %s" % raw)
                transaction.rollback()
                transaction.leave_transaction_management()
            
        return results, errors


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
