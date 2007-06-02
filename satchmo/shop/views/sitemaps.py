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

sitemaps = {
    'category': CategorySitemap,
    'products': ProductSitemap,
}
