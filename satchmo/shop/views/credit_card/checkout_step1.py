####################################################################
# First step in the order process - capture all the demographic info
#####################################################################

from django.shortcuts import render_to_response
from django import http
from django.conf import settings
from django.core import urlresolvers
from django.template import RequestContext, Context
from django.template import loader
from satchmo.shop.models import Cart, CartItem
from satchmo.i18n.models import Country
from satchmo.shop.views.common import save_contact_info, ContactInfoForm, selection
from satchmo.contact.models import Contact
from satchmo.contact.models import Contact

def contact_info(request):
    #First verify that the cart exists and has items
    if request.session.get('cart', False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            return render_to_response('checkout_empty_cart.html', RequestContext(request))
    else:
        return render_to_response('checkout_empty_cart.html', RequestContext(request))

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
    
    if request.session.get('custID', False):
        contact = Contact.objects.get(id=request.session['custID'])
    else:
        contact = None
    
    if request.POST:
        new_data = request.POST.copy()
        form = ContactInfoForm(countries, areas, new_data, initial=init_data)
        
        if form.is_valid():
            if not contact:
                custID = save_contact_info(form.cleaned_data)
                request.session['custID'] = custID
            else:
                custID = save_contact_info(form.cleaned_data, contact)
            #TODO - Create an order here and associate it with a session
            return http.HttpResponseRedirect(urlresolvers.reverse('satchmo_checkout-step2'))
    else:
        if contact:
            #If a person has their contact info, make sure we populate it in the form
            for item in contact.__dict__.keys():
                init_data[item] = getattr(contact,item)
            for item in contact.shipping_address.__dict__.keys():
                init_data["ship_"+item] = getattr(contact.shipping_address,item)
            for item in contact.billing_address.__dict__.keys():
                init_data[item] = getattr(contact.billing_address,item)
            init_data['phone'] = contact.primary_phone.phone
        form = ContactInfoForm(countries, areas, initial=init_data)
    
    return render_to_response('checkout_form.html', {'form': form, 'country': default_country}, RequestContext(request))
