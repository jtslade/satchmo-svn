"""
Each shipping option uses the data in an Order object to calculate the shipping cost and return the value
"""

activeModules = (
("FlatRate","FlatRate"),
("PerItem", "PerItem"))

class FlatRate(object):
    
    flatRateFee = 5.00
    id = "FlatRate"
    
    def __init__(self, cart, contact):
        self.cart = cart
        self.contact = contact
    
    def __str__(self):
        """
        This is mainly helpful for debugging purposes
        """
        return("Flat Rate")
    
    def description(self):
        """
        A basic description that will be displayed to the user when selecting their shipping options
        """
        return("Flat Rate Shipping")
        
    def cost(self):
        """
        Complex calculations can be done here as long as the return value is a dollar figure
        """
        return(self.flatRateFee)
    
    def method(self):
        """
        Describes the actual delivery service (Mail, FedEx, DHL, UPS, etc)
        """
        return("US Mail")
        
    def expectedDelivery(self):
        """
        Can be a plain string or complex calcuation returning an actual date
        """
        return("3 - 4 business days")
        
    def valid(self, order=None):
        """
        Can do complex validation about whether or not this option is valid.  For example,
        may check to see if the recipient is in an allowed country or location.
        """
        return(True)
        
class PerItem(object):
    
    id = "PerItem"
    perItemFee = 10.00
    
    def __init__(self, cart, contact):
        self.cart = cart
        self.contact = contact
    
    def __str__(self):
        """
        This is mainly helpful for debugging purposes
        """
        return("Per Item")
    
    def description(self):
        """
        A basic description that will be displayed to the user when selecting their shipping options
        """
        return("Per Item shipping")
        
    def cost(self):
        """
        Complex calculations can be done here as long as the return value is a dollar figure
        """
        return(self.cart.numItems * self.perItemFee)
    
    def method(self):
        """
        Describes the actual delivery service (Mail, FedEx, DHL, UPS, etc)
        """
        return("US Mail")
        
    def expectedDelivery(self):
        """
        Can be a plain string or complex calcuation returning an actual date
        """
        return("3 - 4 business days")
        
    def valid(self, order=None):
        """
        Can do complex validation about whether or not this option is valid.  For example,
        may check to see if the recipient is in an allowed country or location.
        """
        return(True)
        
        
        