from django.template import Library, Node
from satchmo.product.models import OptionItem
from django.conf import settings

register = Library()

def show_tracker():
    """
    output the google tracker code
    """
    return({"GOOGLE_CODE": settings.GOOGLE_ANALYTICS_CODE})
    
register.inclusion_tag("google-analytics/tracker.html")(show_tracker)

def show_receipt(context):
    """
    Output our receipt in the format the google analytics needs
    """
    return({'Store': settings.SITE_NAME, 
             'order': context['order']})
        
register.inclusion_tag("google-analytics/receipt.html", takes_context=True)(show_receipt)