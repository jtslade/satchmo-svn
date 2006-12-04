import trml2pdf
from django.http import HttpResponse
from django.template import loader, Context
import settings
from satchmo.shop.models import Config
from django.shortcuts import get_object_or_404
from satchmo.contact.models import Order
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache

def invoice(request, id):
    # Create the HttpResponse object with the appropriate PDF headers.
    order = get_object_or_404(Order, pk=id)
    filename = "mystore-invoice.pdf"
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    shopDetails = Config.objects.get(site=settings.SITE_ID)
    t = loader.get_template('pdf/invoice.rml')
    c = Context({
                'filename' : filename,
                'templateDir' : settings.TEMPLATE_DIRS[0],
                'shopDetails' : shopDetails,
                'order' : order
                })
    
    tmpPath =  "~/working-dir/trunk/satchmo/templates/pdf"
    pdf = trml2pdf.parseString(t.render(c))
    response.write(pdf)
    return response
invoice = staff_member_required(never_cache(invoice))