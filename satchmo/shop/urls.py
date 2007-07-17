import os
from django.conf import settings
from satchmo.product.models import Product
from django.conf.urls.defaults import *
from satchmo.payment.paymentsettings import PaymentSettings

#The following views are custom to Satchmo

urlpatterns = getattr(settings, 'SHOP_URLS', [])

urlpatterns += patterns('satchmo.shop.views',
    (r'^category/(?P<slug>[-\w]+)/$', 'category.root'),
    (r'^category/(?P<slug_parent>[-\w]+)/(?P<slug>[-\w]+)/$', 'category.children'),
    (r'^category/([-\w]+/)+(?P<slug_parent>[-\w]+)/(?P<slug>[-\w]+)/$', 'category.children'),
    (r'^cart/add/$', 'cart.add', {}, 'satchmo_cart_add'),
    (r'^cart/add/ajax/$', 'cart.add_ajax', {}, 'satchmo_cart_add_ajax'),
    (r'^cart/(?P<id>\d+)/remove/$', 'cart.remove', {}, 'satchmo_cart_remove'),
    (r'^cart/$', 'cart.display', {}, 'satchmo_cart'),
    (r'^contact/$', 'contact.form', {}, 'satchmo_contact'),
)
#Note with the last category url - this allows category depth to be as deep as we want but the downside
#is that we ignore all but the child and parent category.  In practice this should be ok

urlpatterns += patterns('satchmo.product.views',
    (r'^search/$', 'do_search', {}, 'satchmo_search'),
    (r'^product/(?P<product_name>[-\w]+)/prices/$', 'get_price', {}, 'satchmo_product_prices'),
    (r'^product/(?P<product_name>[-\w]+)/$', 'get_product', {}, 'satchmo_product'),
)

#Dictionaries for generic views used in Satchmo

index_dict = {
    'queryset': Product.objects.filter(active="1").filter(featured="1"),
    'template_object_name': 'all_items',
    'template_name': 'base_index.html',
    'allow_empty': True,
    'paginate_by': 10,
}

urlpatterns += patterns('django.views.generic',
    (r'^$','list_detail.object_list',index_dict),
    (r'^contact/thankyou/$','simple.direct_to_template',{'template':'thanks.html'}),
)

# add checkout urls
urlpatterns += patterns('',
    (r'^checkout/', include('satchmo.payment.urls')),
)

#Make sure thumbnails and images are served up properly when using the dev server
if settings.LOCAL_DEV:
    urlpatterns += patterns('',
        (r'^site_media/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
