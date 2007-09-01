"""
This code is heavily based on samples found here -
http://www.b-list.org/weblog/2006/06/14/django-tips-template-context-processors

It is used to add some common variables to all the templates
"""
from decimal import Decimal
from django.utils.translation import ugettext as _

class NullCart(object):
    """Standin for a real cart when we don't have one yet.  More convenient than testing for null all the time."""
    desc = None
    date_time_created = None
    customer = None
    total=Decimal("0")
    numItems=0

    def add_item(self, chosen_item, number_added):
        pass

    def remove_item(self, chosen_item_id, number_removed):
        pass

    def empty(self):
        pass

    def __str__(self):
        return "NullCart (empty)"
        
    def __iter__(self):
        return iter([])
        
    def __len__(self):
        return 0


def settings(request):
    from django.conf import settings
    from satchmo.shop.models import Config, Cart
    from satchmo.product.models import Category
    from django.core.exceptions import ObjectDoesNotExist
    if Config.objects.count() > 0:
        try:
            shop_config = Config.objects.get(site=settings.SITE_ID)
            shop_name = shop_config.store_name
        except ObjectDoesNotExist:
            shop_name = _("Test Store (No Site id)")
    else:
        shop_name = _("Test Store")
    
    if request.session.get('cart'):
        try:
            tempCart = Cart.objects.get(id=request.session['cart'])
            cart = tempCart
        except Cart.DoesNotExist:
            del request.session['cart']
            cart = NullCart()
    else:
        cart = NullCart()
    all_categories = Category.objects.all()
    
    try:
        enable_adwords = settings.GOOGLE_ADWORDS
    except AttributeError:
        enable_adwords = False
    
    # handle secure requests
    media_url = settings.MEDIA_URL
    secure = request.is_secure()
    if secure:
        try:
            media_url = settings.MEDIA_SECURE_URL
        except AttributeError:
            media_url = media_url.replace('http://','https://')

    return {'shop_base': settings.SHOP_BASE,
             'shop_name': shop_name,
             'media_url': media_url,
             'cart_count': cart.numItems,
             'cart': cart,
             'categories': all_categories,
             'enable_google': settings.GOOGLE_ANALYTICS,
             'enable_adwords': enable_adwords,
             'is_secure' : secure,
             'request' : request,
             }
