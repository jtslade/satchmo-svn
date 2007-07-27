####################################################################
# Last step in the order process - confirm the info and process it
#####################################################################

from django.conf import settings
from django.core import urlresolvers
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import loader, RequestContext, Context
from django.utils.translation import ugettext as _
from satchmo.contact.models import Order, OrderItem, OrderStatus
from satchmo.shop.models import Cart, CartItem, Config
import datetime
from django.template import loader
from django.core.mail import send_mail

def credit_confirm_info(request, payment_module):
    """A view which shows and requires credit card selection"""
    if not request.session.get('orderID'):
        url = urlresolvers.reverse('satchmo_checkout-step1')
        return HttpResponseRedirect(url)

    if request.session.get('cart'):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            template = payment_module.lookup_template('checkout/empty_cart.html')
            return render_to_response(template, RequestContext(request))
    else:
        template = payment_module.lookup_template('checkout/empty_cart.html')
        return render_to_response(template, RequestContext(request))

    orderToProcess = Order.objects.get(id=request.session['orderID'])

    # Check if the order is still valid
    if not orderToProcess.validate(request):
        context = RequestContext(request,
            {'message': _('Your order is no longer valid.')})
        return render_to_response('shop_404.html', context)

    if request.POST:
        #Do the credit card processing here & if successful, empty the cart and update the status
        credit_processor = payment_module.load_processor()
        processor = credit_processor.PaymentProcessor(payment_module)
        processor.prepareData(orderToProcess)
        results, reason_code, msg = processor.process()

        if results:
            tempCart.empty()
            #Update status
            status = OrderStatus()
            status.status = _("Pending")
            status.notes = _("Order successfully submitted")
            status.timestamp = datetime.datetime.now()
            status.order = orderToProcess #For some reason auto_now_add wasn't working right in admin
            status.save()
            #Now, send a confirmation email
            shop_config = Config.objects.get(site=settings.SITE_ID)
            shop_email = shop_config.storeEmail
            shop_name = shop_config.storeName
            t = loader.get_template('email/order_complete.txt')
            c = Context({'order': orderToProcess,
                          'shop_name': shop_name})
            subject = "Thank you for your order from %s" % shop_name
            send_mail(subject, t.render(c), shop_email,
                     [orderToProcess.contact.email], fail_silently=False)
            #Redirect to the success page
            url = payment_module.lookup_url('satchmo_checkout-success')
            return HttpResponseRedirect(url)
        #Since we're not successful, let the user know via the confirmation page
        else:
            errors = msg
    else:
        errors = ''

    template = payment_module.lookup_template('checkout/confirm.html')
    context = RequestContext(request, {
        'order': orderToProcess,
        'errors': errors,
        'checkout_step2': payment_module.lookup_url('satchmo_checkout-step2')})
    return render_to_response(template, context)


