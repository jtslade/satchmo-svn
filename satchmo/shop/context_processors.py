"""
This code is heavily based on samples found here -
http://www.b-list.org/weblog/2006/06/14/django-tips-template-context-processors

It is used to add some common variables to all the templates
"""


def settings(request):
    from django.conf import settings
    from satchmo.shop.models import Config, Cart
    if Config.objects.count() > 0:
        shop_config = Config.objects.all()[0]
        shop_name = shop_config.storeName
    else:
        shop_name = "Test Store"
    return {'shop_base': settings.SHOP_BASE,
             'shop_name': shop_name}