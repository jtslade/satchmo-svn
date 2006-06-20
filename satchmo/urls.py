from django.conf.urls.defaults import *
import os
DIRNAME = os.path.dirname(__file__)

urlpatterns = patterns('',
    # Example:
    # (r'^satchmo/', include('satchmo.apps.foo.urls.foo')),
    (r'^site_media/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(DIRNAME,'static')}),

    # Uncomment this for admin:
     (r'^admin/', include('django.contrib.admin.urls')),
     (r'^shop/$', 'satchmo.shop.views.index'),
)
