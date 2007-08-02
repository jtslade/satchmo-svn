import trml2pdf
from django.http import HttpResponse
from django.template import loader, Context
from django.conf import settings
from satchmo.shop.models import Config
from django.shortcuts import get_object_or_404
from satchmo.contact.models import Order
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache

def displayDoc(request, id, doc):
    # Create the HttpResponse object with the appropriate PDF headers for an invoice or a packing slip
    order = get_object_or_404(Order, pk=id)

    if doc == "invoice":
        filename = "mystore-invoice.pdf"
        template = "invoice.rml"
    elif doc == "packingslip":
        filename = "mystore-packingslip.pdf"
        template = "packing-slip.rml"
    elif doc == "shippinglabel":
        filename = "mystore-shippinglabel.pdf"
        template = "shipping-label.rml"
    else:
        return http.HttpResponseRedirect('/admin')
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    shopDetails = Config.objects.get(site=settings.SITE_ID)
    t = loader.get_template('pdf/%s' % template)
    c = Context({
                'filename' : filename,
                'templateDir' : settings.TEMPLATE_DIRS[0],
                'shopDetails' : shopDetails,
                'order' : order
                })
    pdf = trml2pdf.parseString(t.render(c))
    response.write(pdf)
    return response
displayDoc = staff_member_required(never_cache(displayDoc))

#Note - rendering an image in the file causes problems when running the dev
#server on windows.  Seems to be an issue with trml2pdf
