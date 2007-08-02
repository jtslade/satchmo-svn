"""
Each shipping option uses the data in an Order object to calculate the shipping cost and return the value
"""
from decimal import Decimal
from django.utils.translation import ugettext as _

class Calc(object):

    flatRateFee = Decimal("5.00")
    id = "FlatRate"

    def __init__(self, cart, contact):
        self.cart = cart
        self.contact = contact

    def __str__(self):
        """
        This is mainly helpful for debugging purposes
        """
        return "Flat Rate"

    def description(self):
        """
        A basic description that will be displayed to the user when selecting their shipping options
        """
        return _("Flat Rate Shipping")

    def cost(self):
        """
        Complex calculations can be done here as long as the return value is a dollar figure
        """
        for cartitem in self.cart.cartitem_set.all():
            if cartitem.product.is_shippable:
                return self.flatRateFee
        return Decimal("0.00")

    def method(self):
        """
        Describes the actual delivery service (Mail, FedEx, DHL, UPS, etc)
        """
        return _("US Mail")

    def expectedDelivery(self):
        """
        Can be a plain string or complex calcuation returning an actual date
        """
        return _("3 - 4 business days")

    def valid(self, order=None):
        """
        Can do complex validation about whether or not this option is valid.
        For example, may check to see if the recipient is in an allowed country
        or location.
        """
        return True

