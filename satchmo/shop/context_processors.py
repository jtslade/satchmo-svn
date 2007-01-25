"""
This code is heavily based on samples found here -
http://www.b-list.org/weblog/2006/06/14/django-tips-template-context-processors

It is used to add some common variables to all the templates
"""


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
        cart_count = tempCart.numItems
    else:
        cart_count = 0
    all_categories = Category.objects.all()
    return {'shop_base': settings.SHOP_BASE,
             'shop_name': shop_name,
             'media_url': settings.MEDIA_URL,
             'cart_count': cart_count,
             'categories': all_categories}