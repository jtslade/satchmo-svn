from django.conf.urls.defaults import *
from django.conf import settings
from satchmo.shop.views.sitemaps import sitemaps

if settings.SHOP_BASE == '':
    shopregex = '^'
else:
    shopregex = '^%/' % settings.SHOP_BASE.strip('/')

urlpatterns = []
if hasattr(settings, 'URLS'):
    urlpatterns += settings.URLS

urlpatterns += patterns('',
    (r'^admin/print/(?P<doc>[-\w]+)/(?P<id>\d+)', 'satchmo.shipping.views.displayDoc'),
    (r'^admin/$', 'satchmo.shop.views.admin-portal.home'),
    (r'^admin/', include('django.contrib.admin.urls')),
    (shopregex, include('satchmo.shop.urls')),
    (r'sitemap.xml', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
)

#The following is used to serve up local media files like images
if settings.LOCAL_DEV:
    baseurlregex = r'^static/(?P<path>.*)$'
    urlpatterns += patterns('',
        (baseurlregex, 'django.views.static.serve',
        {'document_root':  settings.MEDIA_ROOT}),
    )

# Remove any URLs whose names have been used already.
names = []
q = [urlpatterns]
while q:
    urls = q.pop()
    for pattern in urls[:]:
        if hasattr(pattern, 'url_patterns'):
            q.append(pattern.url_patterns)
        elif hasattr(pattern, 'name') and pattern.name:
            if pattern.name in names:
                urls.remove(pattern)
            else:
                names.append(pattern.name)
