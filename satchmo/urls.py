from django.conf.urls.defaults import *
import os
from django.conf import settings


urlpatterns = patterns('',
    # Example:
    # (r'^satchmo/', include('satchmo.apps.foo.urls.foo')),
    # Uncomment this for admin:
     (r'^admin/', include('django.contrib.admin.urls')),
     (r'^shop/$', 'satchmo.shop.views.index'),
     (r'^shop/site_media/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)
if settings.LOCAL_DEV:
   baseurlregex = '^' + settings.MEDIA_ROOT[1:] + '/(?P<path>.*)$' 
   urlpatterns += patterns('',
       (baseurlregex, 'django.views.static.serve',
       {'document_root':  settings.MEDIA_ROOT}),
 )
 
 # r'^home/chris/working-dir/satchmo/trunk/satchmo/static/(?P<path>.*)$'