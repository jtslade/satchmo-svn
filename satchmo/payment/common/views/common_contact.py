####################################################################
# First step in the order process - capture all the demographic info
#####################################################################

from django import http
from django.core import urlresolvers
from django.shortcuts import render_to_response
from django.template import loader
from django.template import RequestContext, Context
from satchmo.contact.models import Contact
from satchmo.i18n.models import Country
from satchmo.payment.paymentsettings import PaymentSettings
from satchmo.shop.models import Cart, CartItem
from satchmo.shop.views.common import save_contact_info, selection
from satchmo.payment.common.forms import PaymentContactInfoForm

def contact_info(request):
    """View which collects demographic information from customer."""

    #First verify that the cart exists and has items
    if request.session.get('cart'):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            return render_to_response('checkout/empty_cart.html', RequestContext(request))
    else:
        return render_to_response('checkout/empty_cart.html', RequestContext(request))

    # Get the default country
    if request.GET.get('iso2', False):
        iso2 = request.GET['iso2']
    else:
        iso2 = 'US'
    default_country = Country.objects.get(iso2_code=iso2)
    init_data = {'country': default_country.iso2_code}
    # Create country and state lists
    areas = [(selection,selection)]

    for area in default_country.area_set.all():
        value_to_choose = (area.abbrev, area.name)
        areas.append(value_to_choose)
    countries = [(default_country.iso2_code, default_country.name)]

    for country in Country.objects.filter(display=True):
        country_to_choose = (country.iso2_code, country.name)
        #Make sure the default only shows up once
        if country.iso2_code <> default_country.iso2_code:
            countries.append(country_to_choose)

    contact = None
    if request.session.get('custID', False):
        try:
            contact = Contact.objects.get(id=request.session['custID'])
        except Contact.DoesNotExist:
            pass

    if not contact:
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
            if not contact:
                custID = save_contact_info(form.cleaned_data)
            else:
                custID = save_contact_info(form.cleaned_data, contact)
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
        'country': default_country,
        'paymentmethod_ct': len(PaymentSettings())})
    return render_to_response('checkout/form.html', context)

