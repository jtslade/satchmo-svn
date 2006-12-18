from django.template import RequestContext, Context
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from satchmo.contact.models import Order

def home(request):
    if request.GET.get('legacy', False):
        return render_to_response('admin/index.html', {'title': _('Site administration')}, context_instance=RequestContext(request))
    else:
        pendings =  Order.objects.filter(status='pending').order_by('timeStamp')
        in_process = Order.objects.filter(status='In Process').order_by('timeStamp')
        return render_to_response('admin/portal.html', 
                                    {'pendings': pendings,
                                     'in_process': in_process},
                                 RequestContext(request))
home = staff_member_required(never_cache(home))
