from django.template import RequestContext, Context
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from satchmo.contact.models import Order
from satchmo.contact.models import ORDER_STATUS

def home(request):
    if request.GET.get('legacy', False):
        return render_to_response('admin/index.html', {'title': _('Site administration')}, context_instance=RequestContext(request))
    else:
        pendings =  Order.objects.filter(status=ORDER_STATUS[1][0]).order_by('timeStamp')
        in_process = Order.objects.filter(status=ORDER_STATUS[2][0]).order_by('timeStamp')
        return render_to_response('admin/portal.html', 
                                    {'pendings': pendings,
                                     'in_process': in_process},
                                 RequestContext(request))
home = staff_member_required(never_cache(home))
