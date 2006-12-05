from django.conf.urls.defaults import *
import os
from django.conf import settings

shopregex = '^' + settings.SHOP_BASE[1:] + "/"

urlpatterns = patterns('',
     (r'^admin/print/(?P<doc>[-\w]+)/(?P<id>\d+)', 'satchmo.shipping.views.displayDoc'),
     (r'^admin/', include('django.contrib.admin.urls')),
     (shopregex, include('satchmo.shop.urls')),
)
#The following is used to serve up local media files like images
if settings.LOCAL_DEV:
   baseurlregex = '^' +  "static" + '/(?P<path>.*)$'
   urlpatterns += patterns('',
       (baseurlregex, 'django.views.static.serve',
       {'document_root':  settings.MEDIA_ROOT}),
 )