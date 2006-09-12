from django.template import RequestContext, Context
from django.template import loader
from django import http

def bad_or_missing(request, msg):
    """
    Return an HTTP 404 response for a date request that cannot possibly exist.
    The 'msg' parameter gives the message for the main panel on the page.
    """
    template = loader.get_template('shop_404.html')
    context = RequestContext(request, {'message': msg})
    return http.HttpResponseNotFound(template.render(context))