import sys
from decimal import Decimal
from django.conf import settings
from satchmo.contact.models import OrderItem
from satchmo.discount.models import Discount
from satchmo.tax.modules import simpleTax

def pay_ship_save(new_order, new_data, cart, contact):
    # Save the shipping info
    for module in settings.SHIPPING_MODULES:
        shipping_module = sys.modules[module]
        shipping_instance = shipping_module.Calc(cart, contact)
        if shipping_instance.id == new_data['shipping']:
            new_order.shippingDescription = shipping_instance.description()
            new_order.shippingMethod = shipping_instance.method()
            new_order.shippingCost = shipping_instance.cost()
            new_order.shippingModel = new_data['shipping']

    # Temp setting of the tax and total so we can save it
    new_order.total = Decimal('0.00')
    new_order.tax = Decimal('0.00')
    new_order.sub_total = cart.total
    
    new_order.method = 'Online'

    # Process any discounts
    if new_data.get('discount'):
        discountObject = Discount.objects.filter(code=new_data['discount'])[0]
        if discountObject.freeShipping:
            new_order.shippingCost = Decimal("0.00")
        discount_amount = discountObject.calc(new_order)
    else: 
        discount_amount = Decimal("0.00")
    new_order.discount = discount_amount

    # Now that we have everything, we can see if there's any sales tax to apply
    # Create the appropriate tax model here
    taxProcessor = simpleTax(new_order)
    new_order.tax = taxProcessor.process()

    new_order.total = cart.total + new_order.shippingCost - discount_amount + new_order.tax

    new_order.copyAddresses()

    new_order.save()

    # Add all the items in the cart to the order
    for item in cart.cartitem_set.all():
        new_order_item = OrderItem(order=new_order, item=item.subItem, quantity=item.quantity, 
        unitPrice=item.subItem.unit_price, lineItemPrice=item.line_total)       
        new_order_item.save()

