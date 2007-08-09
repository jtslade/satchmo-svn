from django.template import Library, Node
from django.conf import settings

register = Library()

def show_tracker(secure):
    """
    Output the google tracker code.
    """
    return({"GOOGLE_CODE": settings.GOOGLE_ANALYTICS_CODE,
            "secure" : secure})
    
register.inclusion_tag("google-analytics/tracker.html")(show_tracker)

def show_receipt(context):
    """
    Output our receipt in the format that Google Analytics needs.
    """
    return({'Store': settings.SITE_NAME, 
            'order': context['order']})
        
register.inclusion_tag("google-analytics/receipt.html", takes_context=True)(show_receipt)

