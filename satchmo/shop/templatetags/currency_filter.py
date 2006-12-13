from django import template
from django.conf import settings

register = template.Library()

def currency_formatter(value):
    """ Return a formatted string for currency"""
    return ("%s%.2f" % (settings.CURRENCY, value))
    
register.filter('currency',currency_formatter)