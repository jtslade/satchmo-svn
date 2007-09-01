"""
Tax Modules use the information in the order to calculate any relevant tax
to be applied to the order.

This is called during the checkout process.  You must make sure the order
gets updated with the new tax value
"""
from decimal import Decimal

class simpleTax(object):
    """
    This is just a stub.  However, you can have as complex a tax calculation as
    you'd like here.
    """
    
    def __init__(self, order):
        """
        Any preprocessing steps should go here
        For instance, copying the shipping and billing areas
        """
        pass
        
    def process(self):
        """
        Calculate the tax and return it
        """
        return Decimal("3.5")