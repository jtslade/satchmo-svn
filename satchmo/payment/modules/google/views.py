from django import http
from django.shortcuts import render_to_response
from django.template import RequestContext, Context
from django.template.loader import get_template
from django.utils.translation import ugettext as _
from satchmo.contact.models import Order
from satchmo.payment.common.views import payship
from satchmo.payment.paymentsettings import PaymentSettings
from satchmo.shop.models import Cart
import base64
import hmac
import logging
import sha

log = logging.getLogger("payment.modules.google.processor")

class GoogleCart(object):
    def __init__(self, order, payment_module):
        self.settings = payment_module
        self.cart_xml = self._cart_xml(order)
        self.signature = self._signature()
        
    def _cart_xml(self, order):
        template = get_template(self.settings["CART_XML_TEMPLATE"])
        
        shopping_url = self.settings.lookup_url('satchmo_checkout-success', True, self.settings.SSL)
        edit_url = self.settings.lookup_url('satchmo_cart', True, self.settings.SSL)
        ctx = Context({"order" : order,
                       "continue_shopping_url" : shopping_url,
                       "edit_cart_url" : edit_url,
                       "currency" : self.settings['CURRENCY_CODE'],
                       })
        return template.render(ctx)

    def _signature(self):
        merchkey = self.settings.MERCHANT_KEY
        s = hmac.new(merchkey, self.cart_xml, sha)
        rawsig = s.digest()
        return rawsig

    def encoded_cart(self):
        return base64.encodestring(self.cart_xml)[:-1]

    def encoded_signature(self):
        sig = base64.encodestring(self.signature)[:-1]
        log.debug("Sig is: %s", sig)
        return sig


def pay_ship_info(request):
    return payship.simple_pay_ship_info(request, PaymentSettings().GOOGLE, 'checkout/google/pay_ship.html')
    
def confirm_info(request):
    payment_module = PaymentSettings().GOOGLE

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
    gcart = GoogleCart(order, payment_module)
    log.debug("CART:\n%s", gcart.cart_xml)
    template = payment_module.lookup_template('checkout/google/confirm.html')
    post_url = payment_module.POST_URL % payment_module

    ctx = RequestContext(request, {
        'order': order,
        'post_url': post_url,
        'google_cart' : gcart.encoded_cart(),
        'google_signature' : gcart.encoded_signature()
    })
    
    return render_to_response(template, ctx)