"""
Each shipping option uses the data in an Order object to calculate the shipping cost and return the value
"""

class FlatRate(object):
    
    flatRateFee = 5.00
    
    def __init__(self):
        pass
    
    def __str__(self):
        return("Flat Rate")
        
    def CalcCost(self, CustomerOrder):
        return(self.flatRateFee)

class PerItem(object):
    
    perItemFee = 10.00
    
    def __init__(self):
        pass
        
    def __str__(self):
        return("Cost per item")
        
    def CalcCost(self, CustomerOrder):
        return(CustomerOrder.orderitem_set.count() * self.perItemFee)
        
        