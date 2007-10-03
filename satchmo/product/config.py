from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from satchmo.configuration import *
from satchmo.shop.utils import load_module

PRODUCT_GROUP = ConfigurationGroup('PRODUCT', _('Product Settings'))

#TODO, add to this list when done
#    ('product', 'DownloadableProduct'),
#    ('product', 'BundledProduct'),

config_register([

MultipleStringValue(PRODUCT_GROUP,
    'PRODUCT_TYPES',
    description=_("Product Model Options"),
    default=['product::ConfigurableProduct', 'product::ProductVariation'],
    choices=[('product::ConfigurableProduct', _('Configurable Product')),
             ('product::ProductVariation', _('Product Variation')),
             ('product::CustomProduct', _('Custom Order'))]
    ),
 
StringValue(PRODUCT_GROUP,
    'IMAGE_DIR',
    description=_("Upload Image Dir"),
    help_text=_("""Directory name for storing uploaded images.  
This value will be appended to MEDIA_ROOT.  Do not worry about slashes.  
We can handle it any which way."""),
    default="images")
    
])
    
# --- Load any extra payment modules. ---
extra_product = getattr(settings, 'CUSTOM_PRODUCT_MODULES', ())

for extra in extra_product:
    try:
        load_module("%s.config" % extra)
    except ImportError:
        log.warn('Could not load product module configuration: %s' % extra)
