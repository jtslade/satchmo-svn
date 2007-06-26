from django.contrib.sitemaps import Sitemap
from satchmo.product.models import Category, Item

class CategorySitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.6

    def items(self):
        return Category.objects.all()

class ProductSitemap(Sitemap):
    changefreq = 'weekly'

    def items(self):
        return Item.objects.filter(active=True)

class MainSitemap(Sitemap):
    urls = []

    def items(self):
        return self.urls

    def add_url(self, location, priority=0.5, changefreq='weekly'):
        self.urls.append({
            'location': location,
            'priority': priority,
            'changefreq': changefreq,
        })

    def location(self, obj):
        return obj['location']

    def priority(self, obj):
        return obj['priority']

    def changefreq(self, obj):
        return obj['changefreq']

main_urls = (
    ('/', 1.0, 'hourly'),
    ('/contact/', 1.0, 'monthly'),
    ('/cart/', 0.5, 'monthly'),
    ('/account/login/', 0.8, 'monthly'),
    ('/account/create/', 0.8, 'monthly'),
    ('/account/password_reset/', 0.8, 'monthly'),
)

satchmo_main = MainSitemap()
for url in main_urls:
    satchmo_main.add_url(*url)

sitemaps = {
    'satchmo_main': satchmo_main,
    'category': CategorySitemap,
    'products': ProductSitemap,
}
