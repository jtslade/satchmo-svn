####################################################################
# Last step in the order process - confirm the info and process it
#####################################################################

import datetime
from django import http
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template import loader
from satchmo.shop.models import Cart, CartItem, Config
from satchmo.contact.models import Order, OrderItem, OrderStatus

def confirm_info(request):
    if not request.session.get('orderID', False):
        return http.HttpResponseRedirect('%s/checkout' % (settings.SHOP_BASE))
    if request.session.get('cart', False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            return render_to_response('checkout_empty_cart.html',RequestContext(request))
    else:
        return render_to_response('checkout_empty_cart.html',RequestContext(request))

    orderToProcess = Order.objects.get(id=request.session['orderID'])
    return render_to_response('checkout_confirm-paypal.html',
        {'order': orderToProcess,
         'post_url': settings.PAYPAL_POST_URL,
         'business': settings.PAYPAL_BUSINESS,
         'currency_code': settings.PAYPAL_CURRENCY_CODE,
         'return_address': settings.PAYPAL_RETURN_ADDRESS,
        },
        RequestContext(request))
