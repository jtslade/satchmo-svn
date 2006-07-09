from django.conf.urls.defaults import *
import os
from django.conf import settings


urlpatterns = patterns('',
     (r'^$', 'satchmo.shop.views.index'),
     (r'^site_media/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)

 
