r"""
>>> from satchmo.product.models import *

# Create an option group
>>> optiongroup1 = OptionGroup.objects.create(name="group1", sort_order=0)

# Add an option
>>> option1 = Option.objects.create(optionGroup=optiongroup1, name="option1", value="1", price_change=5, displayOrder=1)
>>> option1
<Option: option1>
>>> option1.value, option1.price_change, option1.displayOrder
('1', 5, 1)

# Modify the option
>>> option1.price_change = 10
>>> option1.displayOrder = 2
>>> option1.save()
>>> option1.value, option1.price_change, option1.displayOrder
('1', 10, 2)

# Retrieve it from the database and verify that its attributes are correct
>>> option1 = Option.objects.get(id=option1.id)
>>> option1.value, option1.price_change, option1.displayOrder
(u'1', Decimal("10"), 2)
"""

if __name__ == "__main__":
    import doctest
    doctest.testmod()

