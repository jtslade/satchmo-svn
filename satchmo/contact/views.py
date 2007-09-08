from django import http
from django import newforms as forms
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render_to_response
from django.template import RequestContext, Context
from django.utils.translation import ugettext_lazy as _, ugettext
from satchmo.contact.models import Contact
import logging

log = logging.getLogger('satchmo.contact.views')

def view(request):
    """View contact info."""
    try:
        user_data = Contact.objects.get(user=request.user.id)
    except Contact.DoesNotExist:
        user_data = None
        
    context = RequestContext(request, {'user_data': user_data})
    return render_to_response('contact/view_profile.html', context)

_deco = user_passes_test(lambda u: not u.is_anonymous(),
                        login_url='/accounts/login/')
view = _deco(view)

def update(request):
    pass
    
def order_history(request):
    pass
    
def order_tracking(request):
    pass