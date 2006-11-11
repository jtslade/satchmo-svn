####################################################################
# Secondstep in the order process - capture the billing method and shipping type
#####################################################################

from django.shortcuts import render_to_response
from django import http
from django.template import RequestContext, Context
from django.template import loader
from satchmo.shop.models import Cart, CartItem, Config
from satchmo.contact.models import Contact
from django.conf import settings
from django import forms
from django.core import validators
from satchmo.discount.models import Discount
from datetime import date
import calendar
from satchmo.shop.views.utils import CreditCard
from satchmo.shipping.modules import *
from satchmo.contact.models import Order, OrderItem, OrderStatus

selection = "Please Select"
credit_types = (
                ('Visa','Visa'),
                ('Mastercard','Mastercard'),
                ('Discover','Discover'),
                )

class payShipManipulator(forms.Manipulator):
    def __init__(self, request):
        year_now = date.today().year

        shipping_options = []
        self.tempCart = Cart.objects.get(id=request.session['cart'])
        self.tempContact = Contact.objects.get(id=request.session['custID'])
        for module in activeModules:
            #Create the list of information the user will see
            shipping_module = eval(module[0])
            shipping_instance = shipping_module(self.tempCart, self.tempContact)
            if shipping_instance.valid():
                t = loader.get_template('shipping_options.html')
                c = Context({
                    'amount': shipping_instance.cost(),
                    'description' : shipping_instance.description(),
                    'method' : shipping_instance.method(),
                    'expected_delivery' : shipping_instance.expectedDelivery() })
                shipping_options.append((shipping_instance.id, t.render(c)))
        self.fields = (
            forms.SelectField(field_name="credit_type", choices=credit_types,is_required=True),
            forms.TextField(field_name="credit_number",length=20, is_required=True, validator_list=[self.isCardValid]),
            forms.SelectField(field_name="month_expires",choices=[(month,month) for month in range(1,13)], is_required=True),
            forms.SelectField(field_name="year_expires",choices=[(year,year) for year in range(year_now,year_now+5)], is_required=True,  
                                                        validator_list=[self.isCardExpired]),
            forms.TextField(field_name="ccv", length=4, is_required=True, validator_list=[validators.isOnlyDigits]),
            forms.RadioSelectField(field_name="shipping",choices=shipping_options, is_required=True),
            forms.TextField(field_name="discount",length=30, validator_list=[self.isValidDiscount]),
            )
            
    def isCardExpired(self,field_data,all_data):
        entered_year = int(all_data["year_expires"])
        entered_month = int(all_data["month_expires"])
        max_day = calendar.monthrange(entered_year,entered_month)[1]
        if date.today() > date(year=entered_year, month=entered_month,day=max_day):
            raise validators.ValidationError("Your card has expired.")
    
    def isCardValid(self, field_data, all_data):
        card = CreditCard(all_data["credit_number"], all_data["ccv"], all_data["credit_type"])
        results, msg = card.verifyCardTypeandNumber()
        if not results:
            raise validators.ValidationError(msg)
    
    def isValidDiscount(self, field_data, all_data):
        discount = Discount.objects.filter(code=field_data).filter(active=True)
        if discount.count() == 0:
            raise validators.ValidationError("Invalid discount")
        valid, msg = discount[0].isValid()
        if not valid:
            raise validators.ValidationError(msg)
        # todo: validate that it can work with these products   
    
    def save(self, newOrder, new_data, cart, contact):
        shipping_module = eval(new_data['shipping'])
        shipping_instance = shipping_module(cart, contact)
        newOrder.shippingDescription = shipping_instance.description()
        newOrder.shippingMethod = shipping_instance.method()
        newOrder.shippingCost = shipping_instance.cost()
        newOrder.shippingModel = new_data['shipping']
        
        if new_data.get('discount',False):
            discountObject = Discount.objects.filter(code=new_data['discount'])[0]
            discount = discountObject.amount
        else: 
            discount = 0
        newOrder.discount = discount
        newOrder.total = float(cart.total) + float(shipping_instance.cost()) - float(discount)
        newOrder.tax = 0
        newOrder.sub_total = cart.total
        newOrder.save()
        newOrder.copyAddresses()
        for item in self.tempCart.cartitem_set.all():
            newOrderItem = OrderItem(order=newOrder, item=item.subItem, quantity=item.quantity, 
                                     unitPrice=item.subItem.unit_price, lineItemPrice=item.line_total)       
            newOrderItem.save()

def pay_ship_info(request):
    #First verify that the customer exists
    if not request.session.get('custID', False):
        return http.HttpResponseRedirect('%s/checkout' % (settings.SHOP_BASE))
    #Verify we still have items in the cart
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            return render_to_response('checkout_empty_cart.html',RequestContext(request))
    else:
        return render_to_response('checkout_empty_cart.html',RequestContext(request))    
    #Verify order info is here
    manipulator = payShipManipulator(request)
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            #data = request.POST.copy()
            manipulator.do_html2python(new_data)
            contact = Contact.objects.get(id=request.session['custID'])
            if request.session.get('orderID',False):
                #order exists so get it
                newOrder = Order.objects.get(id=request.session['orderID'])
                newOrder.contact = contact
                newOrder.removeAllItems() #Make sure any existing items are gone
            else:
                #create a new order
                newOrder = Order(contact=contact)
            #copy data over to the oder
            manipulator.save(newOrder, new_data, tempCart, contact)
            request.session['orderID'] = newOrder.id
            return http.HttpResponseRedirect('%s/checkout/confirm' % (settings.SHOP_BASE))
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('checkout_pay_ship.html', {'form': form},
                                RequestContext(request))    
