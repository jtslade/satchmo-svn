####################################################################
# First step in the order process - capture all the demographic info
#####################################################################

from django import http
from django.conf import settings
from django.core import urlresolvers
from django.shortcuts import render_to_response
from django.template import loader
from django.template import RequestContext, Context
from satchmo.contact.common import get_area_country_options
from satchmo.contact.forms import selection
from satchmo.contact.models import Contact
from satchmo.payment.common.forms import PaymentContactInfoForm
from satchmo.payment.paymentsettings import PaymentSettings
from satchmo.shop.models import Cart, CartItem

def contact_info(request):
    """View which collects demographic information from customer."""

    #First verify that the cart exists and has items
    if request.session.get('cart'):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            return render_to_response('checkout/empty_cart.html', RequestContext(request))
    else:
        return render_to_response('checkout/empty_cart.html', RequestContext(request))

    init_data = {}
    areas, countries, only_country = get_area_country_options(request)

    contact = None
    if request.session.get('custID'):
        try:
            contact = Contact.objects.get(id=request.session['custID'])
        except Contact.DoesNotExist:
            pass

    if contact is None:
        try:
            contact = Contact.objects.get(user=request.user.id)
        except Contact.DoesNotExist:
            pass

    if request.POST:
        new_data = request.POST.copy()
        if not tempCart.is_shippable:
            new_data['copy_address'] = True
        form = PaymentContactInfoForm(countries, areas, new_data,
            initial=init_data)

        if form.is_valid():
            if contact is None and request.user:
                contact = Contact(user=request.user)
            custID = form.save(contact=contact)
            request.session['custID'] = custID
            #TODO - Create an order here and associate it with a session
            paymentmodule = PaymentSettings()[new_data['paymentmethod']]
            url = paymentmodule.lookup_url('satchmo_checkout-step2')
            return http.HttpResponseRedirect(url)
    else:
        if contact:
            #If a person has their contact info, make sure we populate it in the form
            for item in contact.__dict__.keys():
                init_data[item] = getattr(contact,item)
            if contact.shipping_address:
                for item in contact.shipping_address.__dict__.keys():
                    init_data["ship_"+item] = getattr(contact.shipping_address,item)
            if contact.billing_address:
                for item in contact.billing_address.__dict__.keys():
                    init_data[item] = getattr(contact.billing_address,item)
            if contact.primary_phone:
                init_data['phone'] = contact.primary_phone.phone
        form = PaymentContactInfoForm(countries, areas, initial=init_data)

    context = RequestContext(request, {
        'form': form,
        'country': only_country,
        'paymentmethod_ct': len(PaymentSettings())})
    return render_to_response('checkout/form.html', context)

