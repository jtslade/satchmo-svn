####################################################################
# Second step in the order process - capture the billing method and shipping type
#####################################################################

from decimal import Decimal
from django import http
from django import newforms as forms
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from satchmo.contact.models import Contact
from satchmo.contact.models import Order, OrderItem
from satchmo.payment.common.forms import PayShipForm
from satchmo.payment.models import CreditCardDetail
from satchmo.payment.paymentsettings import PaymentSettings
from satchmo.shop.models import Cart
from satchmo.shop.views.utils import CreditCard
from satchmo.tax.modules import simpleTax
from satchmo.discount.models import Discount
import sys

#Import all of the shipping modules
for module in settings.SHIPPING_MODULES:
    __import__(module)

selection = _("Please Select")

def pay_ship_info(request, payment_module):
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
        return render_to_response('checkout/empty_cart.html', RequestContext(request))    
    #Verify order info is here
    if request.POST:
        new_data = request.POST.copy()
        form = PayShipForm(request, payment_module, new_data)
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
            pay_ship_save(newOrder, new_data, tempCart, contact, payment_module)
            request.session['orderID'] = newOrder.id
            url = payment_module.lookup_url('satchmo_checkout-step3')
            return http.HttpResponseRedirect(url)
    else:
        form = PayShipForm(request, payment_module)
    template = payment_module.lookup_template('checkout/pay_ship.html')
    return render_to_response(template, {'form': form}, RequestContext(request))


def pay_ship_save(newOrder, new_data, cart, contact, payment_module):
    # Save the shipping info
    for module in settings.SHIPPING_MODULES:
        shipping_module = sys.modules[module]
        shipping_instance = shipping_module.Calc(cart, contact)
        if shipping_instance.id == new_data['shipping']:
            newOrder.shippingDescription = shipping_instance.description()
            newOrder.shippingMethod = shipping_instance.method()
            newOrder.shippingCost = shipping_instance.cost()
            newOrder.shippingModel = new_data['shipping']
    
    # Temp setting of the tax and total so we can save it
    newOrder.total = Decimal("0")
    newOrder.tax = Decimal("0")
    newOrder.sub_total = cart.total
    if newOrder.notes == None:
        newOrder.notes = ""
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
    
     #Process any discounts
    if new_data.get('discount', False):
        discountObject = Discount.objects.filter(code=new_data['discount'])[0]
        discount_amount = discountObject.calc(newOrder)
        if discountObject.freeShipping:
            newOrder.shippingCost = Decimal("0.00")
    else: 
        discount_amount = Decimal("0.00")
    newOrder.discount = discount_amount
    
    #Calculate the totals
    newOrder.total = cart.total + newOrder.shippingCost - discount_amount + newOrder.tax
    
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
    newOrder.payment = payment_module.KEY
    newOrder.save()
