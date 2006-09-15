"""
Each shipping option uses the data in an Order object to calculate the shipping cost and return the value
"""

activeModules = ["FlatRate","PerItem"]

class FlatRate(object):
    
    flatRateFee = 5.00
    
    def __init__(self):
        pass
    
    def __str__(self):
        return("Flat Rate")
    
    def description(self):
        return("Flat Rate Shipping - $%s" % self.CalcCost())
        
    def CalcCost(self):
        return(self.flatRateFee)

class PerItem(object):
    
    perItemFee = 10.00
    
    def __init__(self):
        pass
        
    def __str__(self):
        return("Cost per item")
    
    def description(self):
        return("Charge per item")
        
    def CalcCost(self):
        return(CustomerOrder.orderitem_set.count() * self.perItemFee)
        
        