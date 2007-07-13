####################################################################
# Second step in the order process - capture the billing method and shipping type
#####################################################################

import sys
from django import http
from django import newforms as forms
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import loader
from django.template import RequestContext, Context
from django.utils.translation import ugettext_lazy as _
from satchmo.shop.models import Cart
from satchmo.contact.models import Contact
from satchmo.discount.models import Discount
from satchmo.contact.models import Order
from satchmo.payment.models import CREDITCHOICES, CreditCardDetail
from satchmo.payment.paymentsettings import PaymentSettings
from satchmo.payment.common.pay_ship import pay_ship_save
from satchmo.shop.views.utils import CreditCard

for module in settings.SHIPPING_MODULES:
    __import__(module)

payment_module = PaymentSettings().PAYPAL

class PayShipForm(forms.Form):
    shipping = forms.ChoiceField(widget=forms.RadioSelect())
    discount = forms.CharField(max_length=30, required=False)

    def __init__(self, request, *args, **kwargs):
        super(PayShipForm, self).__init__(*args, **kwargs)
        
        shipping_options = []
        self.tempCart = Cart.objects.get(id=request.session['cart'])
        self.tempContact = Contact.objects.get(id=request.session['custID'])
        for module in settings.SHIPPING_MODULES:
            #Create the list of information the user will see
            shipping_module = sys.modules[module]
            shipping_instance = shipping_module.Calc(self.tempCart, self.tempContact)
            if shipping_instance.valid():
                t = loader.get_template('shipping_options.html')
                c = Context({
                    'amount': shipping_instance.cost(),
                    'description' : shipping_instance.description(),
                    'method' : shipping_instance.method(),
                    'expected_delivery' : shipping_instance.expectedDelivery() })
                shipping_options.append((shipping_instance.id, t.render(c)))
        self.fields['shipping'].choices = shipping_options        

    def clean_discount(self):
        """ Check if discount exists and is valid. """
        data = self.cleaned_data['discount']
        if data:
            try:
                discount = Discount.objects.get(code=data, active=True)
            except Discount.DoesNotExist:
                raise forms.ValidationError('Invalid discount.')
            valid, msg = discount.isValid(self.tempCart)
            if not valid:
                raise forms.ValidationError(msg)
            # TODO: validate that it can work with these products
        return data


def pay_ship_info(request):
    #First verify that the customer exists
    if not request.session.get('custID', False):
        url = payment_module.lookup_url('satchmo_checkout-step1')
        return http.HttpResponseRedirect(url)
    #Verify we still have items in the cart
    if request.session.get('cart', False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            template = payment_module.lookup_template('checkout/empty_cart.html')
            return render_to_response(template, RequestContext(request))
    else:
        template = payment_module.lookup_template('checkout/empty_cart.html')
        return render_to_response(template, RequestContext(request))

    #Verify order info is here
    if request.POST:
        new_data = request.POST.copy()
        form = PayShipForm(request, new_data)
        if form.is_valid():
            data = form.cleaned_data
            contact = Contact.objects.get(id=request.session['custID'])
            if request.session.get('orderID'):
                try:
                    newOrder = Order.objects.get(id=request.session['orderID'])
                    newOrder.contact = contact
                    newOrder.removeAllItems()
                except Order.DoesNotExist:
                    newOrder = Order(contact=contact)
            else:
                #create a new order
                newOrder = Order(contact=contact)
            #copy data over to the order
            newOrder.payment = 'PayPal'
            pay_ship_save(newOrder, tempCart, contact,
                shipping=data['shipping'], discount=data['discount'])
            request.session['orderID'] = newOrder.id
            url = payment_module.lookup_url('satchmo_checkout-step3')
            return http.HttpResponseRedirect(url)
    else:
        form = PayShipForm(request)

    template = payment_module.lookup_template('checkout/paypal/pay_ship.html')
    return render_to_response(template, {'form': form}, RequestContext(request))

