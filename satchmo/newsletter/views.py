from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from models import NullContact
from satchmo.contact.models import Contact
from satchmo.newsletter import SubscriptionManager
from django.utils.translation import ugettext_lazy as _

from django import newforms as forms

class NewsletterForm(forms.Form):
    full_name = forms.CharField(label=_('Full Name'), max_length=100, required=False)
    email = forms.EmailField(label=_('Email address'), max_length=50, required=True)
    subscribed = forms.BooleanField(label=_('Subscribe'), required=True, initial=True)
    
    def get_contact(self):
        data = self.cleaned_data
        email = data['email']
        full_name = data['full_name']
        status = data['subscribed']
        
        try:
            contact = Contact.objects.get(email=email)
            contact.newsletter = status

        except Contact.DoesNotExist:
            contact = NullContact(full_name, email, status)
        
        return contact

def add_subscription(request, template="newsletter/subscribe_form.html", result_template="newsletter/update_results.html"):
    """Add a subscription and return the results in the requested template."""
    
    return _update(request, True, template, result_template)        

def remove_subscription(request, template="newsletter/unsubscribe_form.html", result_template="newsletter/update_results.html"):
    """Remove a subscription and return the results in the requested template."""

    return _update(request, False, template, result_template)

def update_subscription(request, template="newsletter/update_form.html", result_template="newsletter/update_results.html"):
    """Add a subscription and return the results in the requested template."""

    return _update(request, 'FORM', template, result_template)
    
def _update(request, state, template, result_template):
    """Add a subscription and return the results in the requested template."""
    success = False

    if request.POST:
        form = NewsletterForm(request.POST)
        if form.is_valid():
            contact = form.get_contact()
            if state != "FORM":
                contact.newsletter = state
            result = SubscriptionManager().update_contact(contact)
            success = True
        else:
            result = _('Error, not valid')
    
    else:
        form = NewsletterForm()
        result = ""

    ctx = RequestContext(request, { 
        'result' : result,
        'form' : form
    })
    
    if success:
        return render_to_response(result_template, ctx)
    else:
        return render_to_response(template, ctx)
            