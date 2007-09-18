"""
This code is heavily based on samples found here -
http://www.b-list.org/weblog/2006/06/14/django-tips-template-context-processors

It is used to add some common variables to all the templates
"""
from django.conf import settings as site_settings
from satchmo.product.models import Category
from satchmo.shop.models import Config, Cart

def settings(request):
    shop_config = Config.get_shop_config()
    cart = Cart.get_session_cart(request)
    all_categories = Category.objects.all()
    enable_adwords = getattr(site_settings, 'GOOGLE_ADWORDS', False)
    enable_google_analytics = getattr(site_settings, 'GOOGLE_ANALYTICS', False)

    # handle secure requests
    media_url = site_settings.MEDIA_URL
    secure = request.is_secure()
    if secure:
        try:
            media_url = site_settings.MEDIA_SECURE_URL
        except AttributeError:
            media_url = media_url.replace('http://','https://')

    return {'shop_base': site_settings.SHOP_BASE,
            'shop' : shop_config,
            'shop_name': shop_config.store_name,
            'media_url': media_url,
            'cart_count': cart.numItems,
            'cart': cart,
            'categories': all_categories,
            'enable_google': enable_google_analytics,
            'enable_adwords': enable_adwords,
            'is_secure' : secure,
            'request' : request,
           }
