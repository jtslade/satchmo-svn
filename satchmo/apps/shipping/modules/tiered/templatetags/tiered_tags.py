try:
    from decimal import Decimal
except:
    from django.utils._decimal import Decimal

from django import template
from django.utils.safestring import mark_safe
from shipping.modules.tiered.models import Carrier
from satchmo_utils.templatetags import get_filter_args
from l10n.utils import moneyfmt

register = template.Library()

def tiered_shipping(price, args=''):
    if not args:
        raise template.TemplateSyntaxError('tiered_shipping needs the name of the carrier, as value|tiered_shipping:"carrier"')
    
    try:
        c = Carrier.objects.get(key=args)
    except Carrier.DoesNotExist:
        raise template.TemplateSyntaxError('tiered_shipping needs the name of a valid carrier, could not find carrier "%s"' % args)
    shipping = c.price(Decimal(price))
    
    return mark_safe(moneyfmt(shipping))

register.filter(tiered_shipping)
