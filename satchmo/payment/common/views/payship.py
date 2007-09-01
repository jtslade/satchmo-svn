####################################################################
# Second step in the order process - capture the billing method and shipping type
#####################################################################

from django import http
from django import newforms as forms
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from satchmo.contact.models import Contact
from satchmo.contact.models import Order
from satchmo.payment.common.forms import CreditPayShipForm, SimplePayShipForm
from satchmo.payment.models import CreditCardDetail
from satchmo.payment.paymentsettings import PaymentSettings
from satchmo.payment.common.pay_ship import pay_ship_save
from satchmo.shop.models import Cart
from satchmo.shop.views.utils import CreditCard

#Import all of the shipping modules
for module in settings.SHIPPING_MODULES:
    __import__(module)

selection = _("Please Select")

def credit_pay_ship_info(request, payment_module):
    #First verify that the customer exists
    if not request.session.get('custID', False):
        url = payment_module.lookup_url('satchmo_checkout-step1')
        return http.HttpResponseRedirect(url)

    #Verify we still have items in the cart
    if request.session.get('cart', False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            template = payment_module.lookup_template('checkout/empty_cart.html')
            return render_to_response(template, RequestContext(request))
    else:
        return render_to_response('checkout/empty_cart.html', RequestContext(request))    
    #Verify order info is here
    if request.POST:
        new_data = request.POST.copy()
        form = CreditPayShipForm(request, payment_module, new_data)
        if form.is_valid():
            data = form.cleaned_data
            contact = Contact.objects.get(id=request.session['custID'])

            # Create a new order
            newOrder = Order(contact=contact, payment=payment_module.KEY)
            pay_ship_save(newOrder, tempCart, contact,
                shipping=data['shipping'], discount=data['discount'])
            request.session['orderID'] = newOrder.id

            # Save the credit card information
            cc = CreditCardDetail(order=newOrder, ccv=data['ccv'],
                expireMonth=data['month_expires'],
                expireYear=data['year_expires'],
                creditType=data['credit_type'])
            cc.storeCC(data['credit_number'])
            cc.save()

            url = payment_module.lookup_url('satchmo_checkout-step3')
            return http.HttpResponseRedirect(url)
    else:
        form = CreditPayShipForm(request, payment_module)

    template = payment_module.lookup_template('checkout/pay_ship.html')
    ctx = { 
        'form' : form,
        'PAYMENT_LIVE' : payment_module.PAYMENT_LIVE
    }
    return render_to_response(template, ctx, RequestContext(request))

def simple_pay_ship_info(request, payment_module, template):
    """A pay_ship view which doesn't require a credit card"""
    #First verify that the customer exists
    if not request.session.get('custID', False):
        url = payment_module.lookup_url('satchmo_checkout-step1')
        return http.HttpResponseRedirect(url)
    #Verify we still have items in the cart
    if request.session.get('cart', False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            template = payment_module.lookup_template('checkout/empty_cart.html')
            return render_to_response(template, RequestContext(request))
    else:
        template = payment_module.lookup_template('checkout/empty_cart.html')
        return render_to_response(template, RequestContext(request))

    #Verify order info is here
    if request.POST:
        new_data = request.POST.copy()
        form = SimplePayShipForm(request, payment_module, new_data)
        if form.is_valid():
            data = form.cleaned_data
            contact = Contact.objects.get(id=request.session['custID'])

            # Create a new order
            newOrder = Order(contact=contact, payment=payment_module.KEY)
            pay_ship_save(newOrder, tempCart, contact,
                shipping=data['shipping'], discount=data['discount'])
            request.session['orderID'] = newOrder.id

            url = payment_module.lookup_url('satchmo_checkout-step3')
            return http.HttpResponseRedirect(url)
    else:
        form = SimplePayShipForm(request, payment_module)

    template = payment_module.lookup_template(template)
    ctx = { 
        'form' : form,
        'PAYMENT_LIVE' : payment_module.PAYMENT_LIVE
    }
    return render_to_response(template, ctx, RequestContext(request))
