from django.conf.urls.defaults import *
import os
from django.conf import settings


urlpatterns = patterns('satchmo.shop.views',
     (r'^$', 'index'),
     (r'^product/(?P<slug>[-\w]+)/$','product'), 
)

if settings.LOCAL_DEV:
    urlpatterns += patterns('',
        (r'^site_media/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )