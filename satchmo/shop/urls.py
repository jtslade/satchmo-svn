from django.conf.urls.defaults import *
import os
from django.conf import settings
from satchmo.product.models import Item

urlpatterns = patterns('satchmo.shop.views',
     (r'^category/(?P<slug>[-\w]+)/$','category_root'),
     (r'^category/(?P<slug_parent>[-\w]+)/(?P<slug>[-\w]+)/$','category_children'),
     (r'^category/([-\w]+/)+(?P<slug_parent>[-\w]+)/(?P<slug>[-\w]+)/$','category_children'),
     (r'^cart/(?P<id>\d+)/add/$','add_to_cart'),
     (r'^cart/(?P<id>\d+)/remove/$','remove_from_cart'),
     (r'^cart/$','display_cart'),
     (r'^account/info/$','account_info'),
     (r'^account/logout/$','account_logout'),
)
#Note with the last category url - this allows category depth to be as deep as we want but the downside
#is that we ignore all but the child and parent category.  In practice this should be ok

index_dict = {
    'queryset': Item.objects.filter(active="1").filter(featured="1"),
    'template_object_name': 'all_items', 
    'template_name' : 'base_index.html',
    'allow_empty': True,      
    'paginate_by' : 10,        
}

product_dict = {
    'queryset': Item.objects.filter(active="1"),
    'slug_field' : 'short_name',
    'template_object_name' : 'item', 
    'template_name': 'base_product.html',
}

urlpatterns += patterns('django.views.generic',
                        (r'^$','list_detail.object_list',index_dict),
                        (r'^product/(?P<slug>[-\w]+)/$','list_detail.object_detail',product_dict)
                        )
                        
                        
urlpatterns += patterns('',(r'^account/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}))
    

if settings.LOCAL_DEV:
    urlpatterns += patterns('',
        (r'^site_media/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )