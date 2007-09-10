from django import http
from django import newforms as forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import urlresolvers
from django.shortcuts import render_to_response
from django.template import loader, RequestContext, Context
from django.utils.translation import ugettext_lazy as _, ugettext
from forms import ExtendedContactInfoForm
from satchmo.contact.common import get_area_country_options
from satchmo.contact.forms import selection
from satchmo.contact.models import Contact, Order
from satchmo.shop.views.utils import bad_or_missing
import logging

log = logging.getLogger('satchmo.contact.views')

@login_required
def view(request):
    """View contact info."""
    try:
        user_data = Contact.objects.get(user=request.user.id)
    except Contact.DoesNotExist:
        user_data = None
        
    context = RequestContext(request, {'user_data': user_data})
    return render_to_response('contact/view_profile.html', context)

@login_required
def update(request):
    """Update contact info"""

    init_data = {}
    areas, countries, only_country = get_area_country_options(request)

    contact = Contact.from_request(request, create=False)

    if request.POST:
        new_data = request.POST.copy()
        form = ExtendedContactInfoForm(countries, areas, new_data,
            initial=init_data)

        if form.is_valid():
            if contact is None and request.user:
                contact = Contact(user=request.user)
            custID = form.save(contact=contact)
            request.session['custID'] = custID
            url = urlresolvers.reverse('satchmo_account_info')
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
        form = ExtendedContactInfoForm(countries, areas, initial=init_data)

    context = RequestContext(request, {
        'form': form,
        'country': only_country})
    return render_to_response('contact/update_form.html', context)
        
@login_required
def order_history(request):
    orders = None
    contact = Contact.from_request(request, create=False)
    if contact:
        try:
            orders = Order.objects.filter(contact=contact).order_by('-timestamp')
        except Order.DoesNotExist:
            pass

    ctx = RequestContext(request, {
        'contact' : contact,
        'orders' : orders})

    return render_to_response('contact/order_history.html', ctx)
    
    
@login_required
def order_tracking(request, order_id):
    order = None
    contact = Contact.from_request(request, create=False)
    if contact:
        try:
            order = Order.objects.get(id__exact=order_id, contact=contact)
        except Order.DoesNotExist:
            pass
    
    if order is None:
        return bad_or_missing(request, _("The order you have requested doesn't exist, or you don't have access to it."))

    ctx = RequestContext(request, {
        'contact' : contact,
        'order' : order})
        
    return render_to_response('contact/order_tracking.html', ctx)

