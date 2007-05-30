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
from satchmo.payment.paymentsettings import PaymentSettings

payment_module = PaymentSettings().PAYPAL

def confirm_info(request):
    if not request.session.get('orderID', False):
        url = payment_module.lookup_url('satchmo_checkout-step1')
        return http.HttpResponseRedirect(url)
    if request.session.get('cart', False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            template = payment_module.lookup_template('checkout/empty_cart.html')
            return render_to_response(template, RequestContext(request))
    else:
        template = payment_module.lookup_template('checkout/empty_cart.html')
        return render_to_response(template, RequestContext(request))

    order = Order.objects.get(id=request.session['orderID'])
    template = payment_module.lookup_template('checkout/paypal/confirm.html')
    return render_to_response(template,
        {'order': order,
         'post_url': payment_module.POST_URL,
         'business': payment_module.BUSINESS,
         'currency_code': payment_module.CURRENCY_CODE,
         'return_address': payment_module.RETURN_ADDRESS,
        },
        RequestContext(request))
