from django import template
#from django.conf import settings
#from django.template import Context, Template

register = template.Library()

@register.inclusion_tag('contact/_addressblock.html')
def addressblock(address):
    """Output an address as a text block"""
    return {"address" : address}
    