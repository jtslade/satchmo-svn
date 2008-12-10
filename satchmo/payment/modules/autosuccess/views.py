from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import never_cache
from satchmo.configuration import config_get_group
from satchmo.payment.utils import pay_ship_save, record_payment
from satchmo.shop.models import Cart
from satchmo.shop.models import Order, Contact, OrderPayment
from satchmo.utils.dynamic import lookup_url, lookup_template

import logging

log = logging.getLogger('autosuccess.views')

def one_step(request):
    payment_module = config_get_group('PAYMENT_AUTOSUCCESS')

    #First verify that the customer exists
    try:
        contact = Contact.objects.from_request(request, create=False)
    except Contact.DoesNotExist:
        url = lookup_url(payment_module, 'satchmo_checkout-step1')
        return HttpResponseRedirect(url)
    #Verify we still have items in the cart
    tempCart = Cart.objects.from_request(request)
    if tempCart.numItems == 0:
        template = lookup_template(payment_module, 'checkout/empty_cart.html')
        return render_to_response(template, RequestContext(request))
            
    # Create a new order
    newOrder = Order(contact=contact)
    pay_ship_save(newOrder, tempCart, contact,
        shipping="", discount="")
        
    request.session['orderID'] = newOrder.id
        
    newOrder.add_status(status='Pending', notes = "Order successfully submitted")

    record_payment(newOrder, payment_module, amount=newOrder.balance)
    
    tempCart.empty()
    success = lookup_url(payment_module, 'satchmo_checkout-success')
    return HttpResponseRedirect(success)
one_step = never_cache(one_step)
