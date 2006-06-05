from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    # (r'^satchmo/', include('satchmo.apps.foo.urls.foo')),

    # Uncomment this for admin:
     (r'^admin/', include('django.contrib.admin.urls')),
)
