from django.conf.urls.defaults import *
import os
from django.conf import settings


urlpatterns = patterns('satchmo.shop.views',
     (r'^$', 'index'),
     (r'^product/(?P<slug>[-\w]+)/$','product'),
     (r'^category/(?P<slug>[-\w]+)/$','category_root'),
     (r'^category/(?P<slug_parent>[-\w]+)/(?P<slug>[-\w]+)/$','category_children'),
     (r'^category/([-\w]+/)+(?P<slug_parent>[-\w]+)/(?P<slug>[-\w]+)/$','category_children'),
     (r'^cart/(?P<id>\d+)/add/$','add_to_cart'),
     (r'^cart/$','display_cart'),
)
#Note with the last url - this allows category depth to be as deep as we want but the downside
#is that we ignore all but the child and parent category.  In practice this should be ok
if settings.LOCAL_DEV:
    urlpatterns += patterns('',
        (r'^site_media/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )