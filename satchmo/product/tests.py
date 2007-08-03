r"""
>>> from decimal import Decimal
>>> from django import db
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

# Retrieve it from the database and verify that its attributes are correct
>>> option1 = Option.objects.get(id=option1.id)
>>> ((option1.value, option1.price_change, option1.displayOrder) ==
... (u'1', 10, 2))
True


>>> sizes = OptionGroup.objects.create(name="sizes", sort_order=1)
>>> option_small = Option.objects.create(optionGroup=sizes, name="Small", value="small", displayOrder=1)
>>> option_large = Option.objects.create(optionGroup=sizes, name="Large", value="large", displayOrder=2, price_change=1)

>>> colors = OptionGroup.objects.create(name="colors", sort_order=2)
>>> option_black = Option.objects.create(optionGroup=colors, name="Black", value="black", displayOrder=1)
>>> option_white = Option.objects.create(optionGroup=colors, name="White", value="white", displayOrder=2, price_change=3)

>>> option_white.price_change = 5
>>> option_white.displayOrder = 2
>>> option_white.save()

>>> option_white.value = "black"
>>> try:
...     option_white.save()
...     assert False
... except db.IntegrityError: pass
>>> db.transaction.rollback()

>>> option_white = Option.objects.get(id=option_white.id)
>>> ((option_white.value, option_white.price_change, option_white.displayOrder)
... == (u'white', 5, 2))
True
>>> option_white.value, option_white.price_change, option_white.displayOrder

>>> django_shirt = Product.objects.create(slug="django-shirt", full_name="Django shirt")
>>> shirt_price = Price.objects.create(product=django_shirt, price="10.5")
>>> django_config = ConfigurableProduct(product=django_shirt)
>>> django_config.option_group.add(sizes, colors)
>>> django_config.option_group.order_by('name')
[<OptionGroup: colors>, <OptionGroup: sizes>]
>>> django_config.save()

>>> product_white_small = Product.objects.create(slug="django-shirt-white-small", full_name="Django Shirt (White/Small)")
>>> pv_white_small = ProductVariation.objects.create(product=product_white_small, parent=django_config)
>>> pv_white_small.options.add(option_white, option_small)
>>> pv_white_small.unit_price == Decimal("15.50")
True
"""

if __name__ == "__main__":
    import doctest
    doctest.testmod()

