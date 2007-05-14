####################################################################
# Second step in the order process - capture the billing method and shipping type
#####################################################################

import datetime
import calendar
import sys
from decimal import Decimal
from django import http
from django import newforms as forms
from django.conf import settings
from django.core import urlresolvers
from django.shortcuts import render_to_response
from django.template import loader
from django.template import RequestContext, Context
from satchmo.shop.models import Cart
from satchmo.contact.models import Contact
from satchmo.discount.models import Discount
from satchmo.contact.models import Order, OrderItem
from satchmo.payment.models import CREDITCHOICES, CreditCardDetail
from satchmo.shop.views.utils import CreditCard
from satchmo.tax.modules import simpleTax

for module in settings.SHIPPING_MODULES:
    __import__(module)

selection = "Please Select"
#Import all of the shipping modules


class PayShipForm(forms.Form):
    credit_type = forms.ChoiceField(choices=CREDITCHOICES)
    credit_number = forms.CharField(max_length=20)
    month_expires = forms.ChoiceField(choices=[(month,month) for month in range(1,13)])
    year_expires = forms.ChoiceField()
    ccv = forms.IntegerField() # find min_length
    shipping = forms.ChoiceField(widget=forms.RadioSelect())
    discount = forms.CharField(max_length=30, required=False)

    def __init__(self, request, *args, **kwargs):
        super(PayShipForm, self).__init__(*args, **kwargs)
        year_now = datetime.date.today().year
        self.fields['year_expires'].choices = [(year, year) for year in range(year_now, year_now+5)]
        
        shipping_options = []
        tempCart = Cart.objects.get(id=request.session['cart'])
        tempContact = Contact.objects.get(id=request.session['custID'])

        for module in settings.SHIPPING_MODULES:
            #Create the list of information the user will see
            shipping_module = sys.modules[module]
            shipping_instance = shipping_module.Calc(tempCart, tempContact)
            if shipping_instance.valid():
                t = loader.get_template('shipping_options.html')
                c = Context({
                    'amount': shipping_instance.cost(),
                    'description' : shipping_instance.description(),
                    'method' : shipping_instance.method(),
                    'expected_delivery' : shipping_instance.expectedDelivery() })
                shipping_options.append((shipping_instance.id, t.render(c)))
        self.fields['shipping'].choices = shipping_options        

    def clean_credit_number(self):
        """ Check if credit card is valid. """
        card = CreditCard(self.cleaned_data['credit_number'], self.cleaned_data['credit_type'])
        results, msg = card.verifyCardTypeandNumber()
        if not results:
            raise forms.ValidationError(msg)

    def clean_year_expires(self):
        """ Check if credit card has expired. """
        month = int(self.cleaned_data['month_expires'])
        year = int(self.cleaned_data['year_expires'])
        max_day = calendar.monthrange(year, month)[1]
        if datetime.date.today() > datetime.date(year=year, month=month, day=max_day):
            raise forms.ValidationError('Your card has expired.')
            
    def clean_discount(self):
        """ Check if discount exists. """
        data = self.cleaned_data['discount']
        if data:
            discount = Discount.objects.filter(code=data).filter(active=True)
            if discount.count() == 0:
                raise forms.ValidationError('Invalid discount.')
            valid, msg = discount[0].isValid()
            if not valid:
                raise forms.ValidationError(msg)
            # TODO: validate that it can work with these products


def pay_ship_info(request):
    #First verify that the customer exists
    if not request.session.get('custID', False):
        return http.HttpResponseRedirect(urlresolvers.reverse('satchmo_checkout-step1'))
    #Verify we still have items in the cart
    if request.session.get('cart', False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            return render_to_response('checkout_empty_cart.html', RequestContext(request))
    else:
        return render_to_response('checkout_empty_cart.html', RequestContext(request))    
    #Verify order info is here
    if request.POST:
        new_data = request.POST.copy()
        form = PayShipForm(request, new_data)
        if form.is_valid():
            contact = Contact.objects.get(id=request.session['custID'])
            if request.session.get('orderID', False):
                #order exists so get it
                newOrder = Order.objects.get(id=request.session['orderID'])
                newOrder.contact = contact
                newOrder.removeAllItems() #Make sure any existing items are gone
            else:
                #create a new order
                newOrder = Order(contact=contact)
            #copy data over to the order
            save(newOrder, new_data, tempCart, contact)
            request.session['orderID'] = newOrder.id
            return http.HttpResponseRedirect(urlresolvers.reverse('satchmo_checkout-step3'))
    else:
        form = PayShipForm(request)
    return render_to_response('checkout_pay_ship.html', {'form': form},
                                RequestContext(request))


def save(newOrder, new_data, cart, contact):
    # Save the shipping info
    for module in settings.SHIPPING_MODULES:
        shipping_module = sys.modules[module]
        shipping_instance = shipping_module.Calc(cart, contact)
        if shipping_instance.id == new_data['shipping']:
            newOrder.shippingDescription = shipping_instance.description()
            newOrder.shippingMethod = shipping_instance.method()
            newOrder.shippingCost = shipping_instance.cost()
            newOrder.shippingModel = new_data['shipping']
    
    #Process any discounts
    if new_data.get('discount', False):
        discountObject = Discount.objects.filter(code=new_data['discount'])[0]
        discount = discountObject.amount
    else: 
        discount = Decimal("0")
    newOrder.discount = discount
    
    # Temp setting of the tax and total so we can save it
    newOrder.total = Decimal("0")
    newOrder.tax = Decimal("0")
    newOrder.sub_total = cart.total
    newOrder.save()
    newOrder.copyAddresses()
    
    #Add all the items in the cart to the order
    for item in cart.cartitem_set.all():
        newOrderItem = OrderItem(order=newOrder, item=item.subItem, quantity=item.quantity, 
        unitPrice=item.subItem.unit_price, lineItemPrice=item.line_total)       
        newOrderItem.save()
    
    #Now that we have everything, we can see if there's any sales tax to apply
    # Create the appropriate tax model here
    taxProcessor = simpleTax(newOrder)
    newOrder.tax = taxProcessor.process()
    #Calculate the totals
    newOrder.total = cart.total + shipping_instance.cost() - discount + newOrder.tax
    
    # Save the credit card information
    cc = CreditCardDetail()
    cc.storeCC(new_data['credit_number'])
    cc.order = newOrder
    cc.expireMonth = new_data['month_expires']
    cc.expireYear = new_data['year_expires']
    cc.ccv = new_data['ccv']
    cc.creditType = new_data['credit_type']
    cc.save()
    
    # Make final additions to the order info
    newOrder.method = "Online"
    newOrder.payment = "Credit Card"
    newOrder.save()
