"""
This code is heavily based on samples found here -
http://www.b-list.org/weblog/2006/06/14/django-tips-template-context-processors

It is used to add some common variables to all the templates
"""
from decimal import Decimal
 
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


def settings(request):
    from django.conf import settings
    from satchmo.shop.models import Config, Cart
    from satchmo.product.models import Category
    from django.core.exceptions import ObjectDoesNotExist
    if Config.objects.count() > 0:
        try:
            shop_config = Config.objects.get(site=settings.SITE_ID)
            shop_name = shop_config.storeName
        except ObjectDoesNotExist:
            shop_name = "Test Store (No Site id)"
    else:
        shop_name = "Test Store"
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        cart = tempCart
    else:
        cart = NullCart()
    all_categories = Category.objects.all()
    return {'shop_base': settings.SHOP_BASE,
             'shop_name': shop_name,
             'media_url': settings.MEDIA_URL,
             'cart_count': cart.numItems,
             'cart': cart,
             'categories': all_categories,
             'enable_google': settings.GOOGLE_ANALYTICS}
