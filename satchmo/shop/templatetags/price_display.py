from django.template import Library, Node
from satchmo.product.models import OptionItem
from django.conf import settings

register = Library()

def option_price(option_item):
    """
    Returns the price as (+$1.00)
    or (-$1.00) depending on the sign of the price change
    The currency symbol is set in the settings.py file
    """
    output = ""
    if option_item.price_change < 0:
        output = "(- %s%s)" % (settings.CURRENCY, abs(option_item.price_change))
    if option_item.price_change > 0:
        output = "(+ %s%s)" % (settings.CURRENCY, option_item.price_change)
    return output

register.simple_tag(option_price)