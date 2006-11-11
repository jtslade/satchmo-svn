####################################################################
# Last step in the order process - confirm the info and process it
#####################################################################

from django.shortcuts import render_to_response
from django import http
from django.template import RequestContext
from django.template import loader
from satchmo.shop.models import Cart, CartItem, Config
from django.conf import settings
from satchmo.contact.models import Order, OrderItem, OrderStatus

def confirm_info(request):
    if not request.session.get('orderID', False):
        return http.HttpResponseRedirect('%s/checkout' % (settings.SHOP_BASE))
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            return render_to_response('checkout_empty_cart.html',RequestContext(request))
    else:
        return render_to_response('checkout_empty_cart.html',RequestContext(request))    
    if request.POST:
        #Do the credit card processing here
        tempCart.empty()
        #Convert order status
        #Redirect to the success page
        return http.HttpResponseRedirect('%s/checkout/success' % (settings.SHOP_BASE))
    else:
        order = Order.objects.get(id=request.session['orderID'])
        return render_to_response('checkout_confirm.html', {'order': order}, RequestContext(request))