from django.conf.urls.defaults import *

urlpatterns = patterns('satchmo.product.views',
(r'^(?P<product_slug>[-\w]+)/prices/$', 'get_price', {}, 'satchmo_product_prices'),
(r'^(?P<product_slug>[-\w]+)/$', 'get_product', {}, 'satchmo_product'),
(r'^inventory/edit/$', 'edit_inventory', {}, 'satchmo_admin_edit_inventory'),
)
