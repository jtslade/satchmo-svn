import sys
from decimal import Decimal
from django.conf import settings
from satchmo.configuration import config_value
from satchmo.contact.models import OrderItem
from satchmo.discount.models import Discount
from satchmo.shop.utils import load_module
from satchmo.tax.modules import simpleTax
import logging

log = logging.getLogger('pay_ship')

def pay_ship_save(new_order, cart, contact, shipping, discount):
    # Set a default for when no shipping module is used
    new_order.shipping_cost = Decimal("0.00")

    # Save the shipping info
    for module in config_value('SHIPPING','MODULES'):
        shipping_module = load_module(module)
        shipping_instance = shipping_module.Calc(cart, contact)
        if shipping_instance.id == shipping:
            new_order.shipping_description = shipping_instance.description().encode()
            new_order.shipping_method = shipping_instance.method()
            new_order.shipping_cost = shipping_instance.cost()
            new_order.shipping_model = shipping

    # Temp setting of the tax and total so we can save it
    new_order.total = Decimal('0.00')
    new_order.tax = Decimal('0.00')
    new_order.sub_total = cart.total

    new_order.method = 'Online'

    # Process any discounts
    if discount:
        discountObject = Discount.objects.filter(code=discount)[0]
        if discountObject.freeShipping:
            new_order.shipping_cost = Decimal("0.00")
        discount_amount = discountObject.calc(new_order)
    else:
        discount_amount = Decimal("0.00")
    new_order.discount = discount_amount

    # Now that we have everything, we can see if there's any sales tax to apply
    # Create the appropriate tax model here
    taxProcessor = simpleTax(new_order)
    new_order.tax = taxProcessor.process()

    new_order.total = cart.total + new_order.shipping_cost - discount_amount + new_order.tax

    new_order.save()

    # Add all the items in the cart to the order
    for item in cart.cartitem_set.all():
        new_order_item = OrderItem(order=new_order, product=item.product, quantity=item.quantity,
        unit_price=item.unit_price, line_item_price=item.line_total)
        new_order_item.save()


