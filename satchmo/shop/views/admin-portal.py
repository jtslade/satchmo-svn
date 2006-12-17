from django.template import RequestContext, Context
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache

def home(request):
    if request.GET.get('legacy', False):
        return render_to_response('admin/index.html', {'title': _('Site administration')}, context_instance=RequestContext(request))
    else:
        return render_to_response('admin/portal.html', RequestContext(request))
home = staff_member_required(never_cache(home))
