from django.template import RequestContext, Context
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from satchmo.contact.models import Order
from satchmo.contact.models import ORDER_STATUS
from django.utils.translation import gettext_lazy as _

def home(request):
    title = _("Site Administration")
    if request.GET.get('legacy', False) or not request.user.is_superuser:
        return render_to_response('admin/index.html', {'title': title}, context_instance=RequestContext(request))
    else:
        pending = str(ORDER_STATUS[1][1])
        inProcess = str(ORDER_STATUS[2][1])
        pendings =  Order.objects.filter(status=pending).order_by('timeStamp')
        in_process = Order.objects.filter(status=inProcess).order_by('timeStamp')
        return render_to_response('admin/portal.html', 
                                    {'pendings': pendings,
                                     'in_process': in_process,
                                     'title': title},
                                 RequestContext(request))
home = staff_member_required(never_cache(home))
