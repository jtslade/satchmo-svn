r"""
>>> import datetime
>>> from satchmo.discount.models import *

# Create a basic discount
>>> start = datetime.date(2006, 10, 1)
>>> end = datetime.date(2007, 10, 1)
>>> disc1 = Discount.objects.create(description="New Sale", code="BUYME", amount="5.00", allowedUses=10,
... numUses=0, minOrder=5, active=True, startDate=start, endDate=end, freeShipping=False)
>>> disc1.isValid()
(True, 'Valid')

#Change start date to the future
>>> start = datetime.date(2007, 5, 1)                                           
>>> disc1.startDate = start
>>> disc1.isValid()
(False, 'This coupon is not active yet.')

#Change end date to the past
>>> end = datetime.date(2006, 12, 31)
>>> disc1.endDate = end
>>> disc1.isValid()
(False, 'This coupon is not active yet.')

"""

if __name__ == "__main__":
    import doctest
    doctest.testmod()