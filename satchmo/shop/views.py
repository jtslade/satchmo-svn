# Create your views here.

from django.shortcuts import render_to_response
from django import http
from django.template import RequestContext, loader
from satchmo.product.models import Item, Category

def bad_or_missing(request, msg):
    """
    Return an HTTP 404 response for a date request that cannot possibly exist.
    The 'msg' parameter gives the message for the main panel on the page.
    """
    template = loader.get_template('shop_404.html')
    context = RequestContext(request, {'message': msg})
    return http.HttpResponseNotFound(template.render(context))


def index(request):
    featured_items = Item.objects.filter(active="1").filter(featured="1")
    return render_to_response('base_index.html', {'all_items': featured_items})

def product(request, slug):
    try:
        item = Item.objects.filter(active="1").get(short_name=slug)
    except Item.DoesNotExist:
        return bad_or_missing(request, 'The product you have requested does '
                'not exist.')
    return render_to_response('base_product.html',{'item':item})
        
def category_root(request, slug):
    try:
        category = Category.objects.filter(slug=slug)[0]
    except IndexError:
        return bad_or_missing(request, 'The category you have requested does '
            'not exist.')
    return render_to_response('base_category.html',{'category':category})

def category_children(request, slug_parent, slug):
    try:
        parent = Category.objects.filter(slug=slug_parent)[0]
    except IndexError:
        return bad_or_missing(request, 'The category you have requested does '
            'not exist.')
    try:
        category = parent.child.filter(slug=slug)[0]
    except IndexError:
        return bad_or_missing(request, 'The category you have requested does '
            'not exist.')
            
    return render_to_response('base_category.html',{'category':category})