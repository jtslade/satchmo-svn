from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext, Context
from django.utils.translation import ugettext as _
from satchmo.contact.models import Order
from satchmo.payment.common.views import payship
from satchmo.payment.paymentsettings import PaymentSettings
from satchmo.shop.models import Cart
import datetime

def pay_ship_info(request):
    return payship.simple_pay_ship_info(request, PaymentSettings().PAYPAL, 'checkout/paypal/pay_ship.html')

def confirm_info(request):
    payment_module = PaymentSettings().PAYPAL

    if not request.session.get('orderID'):
        url = payment_module.lookup_url('satchmo_checkout-step1')
        return HttpResponseRedirect(url)

    if request.session.get('cart'):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            template = payment_module.lookup_template('checkout/empty_cart.html')
            return render_to_response(template, RequestContext(request))
    else:
        template = payment_module.lookup_template('checkout/empty_cart.html')
        return render_to_response(template, RequestContext(request))

    order = Order.objects.get(id=request.session['orderID'])

    # Check if the order is still valid
    if not order.validate(request):
        context = RequestContext(request,
            {'message': _('Your order is no longer valid.')})
        return render_to_response('shop_404.html', context)

    template = payment_module.lookup_template('checkout/paypal/confirm.html')
    ctx = RequestContext(request, {'order': order,
     'post_url': payment_module.POST_URL,
     'business': payment_module.BUSINESS,
     'currency_code': payment_module.CURRENCY_CODE,
     'return_address': payment_module.RETURN_ADDRESS,
     'PAYMENT_LIVE' : payment_module.PAYMENT_LIVE,
    })

    return render_to_response(template, ctx)

