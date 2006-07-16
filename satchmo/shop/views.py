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
    #Display the basic product detail page
    try:
        item = Item.objects.filter(active="1").get(short_name=slug)
    except Item.DoesNotExist:
        return bad_or_missing(request, 'The product you have requested does '
                'not exist.')
    return render_to_response('base_product.html',{'item':item})
        
def category_root(request, slug):
    #Display the category page if we're not dealing with a child category
    try:
        category = Category.objects.filter(slug=slug)[0]
    except IndexError:
        return bad_or_missing(request, 'The category you have requested does '
            'not exist.')
    return render_to_response('base_category.html',{'category':category})

def category_children(request, slug_parent, slug):
    #Display the category if it is a child
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

def display_cart(request):
    #Show the items in the cart
    cart_list = []
    if request.session.get('cart_items',False):
        for cart_item in request.session['cart_items']:
            item = Item.objects.get(id=cart_item)
            cart_list.append(item)
        return render_to_response('base_cart.html', {'all_items': cart_list})
    else:
        return render_to_response('base_cart.html', {'all_items' : []})

def add_to_cart(request, id):
    #Add an item to the session/cart
    chosenOptions = []
    try:
        product = Item.objects.get(pk=id)
    except Item.DoesNotExist:
        return bad_or_missing(request, 'The product you have requested does '
                'not exist.')
    for option in product.option_group.all():
        chosenOptions.append('%s:%s' % (option.name,request.POST[option.name]))
    #Need to figure out best way to add to the session
    if request.session.get('cart_items',False):
        currentItems = request.session['cart_items']
        newItems = currentItems + [id]
        request.session['cart_items'] = newItems
    else:
        request.session['cart_items'] = [id]
    return http.HttpResponseRedirect('/shop/cart')