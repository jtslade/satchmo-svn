####################################################################
# Last step in the order process - confirm the info and process it
#####################################################################

from django import http
from django.conf import settings
from django.core import urlresolvers
from django.shortcuts import render_to_response
from django.template import loader
from django.template import RequestContext
from django.utils.translation import gettext_lazy as _
from satchmo.contact.models import Order, OrderItem, OrderStatus
from satchmo.shop.models import Cart, CartItem, Config
import datetime
import sys

def confirm_info(request, paymentsettings):    
    if not request.session.get('orderID', False):
        return http.HttpResponseRedirect(urlresolvers.reverse('satchmo_checkout-step1'))
        
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            template = paymentsettings.lookup_template('checkout/empty_cart.html')
            return render_to_response(template, RequestContext(request))
    else:
        template = paymentsettings.lookup_template('checkout/empty_cart.html')
        return render_to_response(template, RequestContext(request))    
        
    orderToProcess = Order.objects.get(id=request.session['orderID'])
    
    if request.POST:
        #Do the credit card processing here & if successful, empty the cart and update the status
        credit_processor = paymentsettings.load_processor()
        processor = credit_processor.PaymentProcessor(paymentsettings)
        processor.prepareData(orderToProcess)
        results, reason_code, msg = processor.process()
        
        if results:
            tempCart.empty()
            #Update status
            status = OrderStatus()
            status.status = "Pending"
            status.notes = _("Order successfully submitted")
            status.timeStamp = datetime.datetime.now()
            status.order = orderToProcess #For some reason auto_now_add wasn't working right in admin
            status.save()
            #del request.session['orderID']
            #Redirect to the success page
            redirectUrl = paymentsettings.lookup_url('satchmo_checkout-success')
            return http.HttpResponseRedirect(redirectUrl)
        #Since we're not successful, let the user know via the confirmation page
        else:
            errors = msg
            template = paymentsettings.lookup_template('checkout/confirm.html')
            return render_to_response(template, {'order': orderToProcess, 'errors': errors}, RequestContext(request))
    else:
        template = paymentsettings.lookup_template('checkout/confirm.html')
        return render_to_response(template, {'order': orderToProcess}, RequestContext(request))
