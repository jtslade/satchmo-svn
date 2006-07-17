# Create your views here.

from django.shortcuts import render_to_response
from django import http
from django.template import RequestContext, loader
from satchmo.product.models import Item, Category
from satchmo.shop.models import Cart, CartItem
from sets import Set

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
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        return render_to_response('base_cart.html', {'all_items': tempCart.cartitem_set.all()})
    else:
        return render_to_response('base_cart.html', {'all_items' : []})

def add_to_cart(request, id):
    #Add an item to the session/cart
    chosenOptions = Set()
    try:
        product = Item.objects.get(pk=id)
    except Item.DoesNotExist:
        return bad_or_missing(request, 'The product you have requested does '
                'not exist.')
    for option in product.option_group.all():
        chosenOptions.add('%s-%s' % (option.name,request.POST[option.name]))
    #Now get the appropriate sub_item
    chosenItem = product.get_sub_item(chosenOptions)
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
    else:
        tempCart = Cart()
    tempCart.save() #need to make sure there's an id
    newItem = CartItem(cart=tempCart, subItem=chosenItem, quantity=1)
    newItem.save()
    tempCart.save()
    request.session['cart'] = tempCart.id

    return http.HttpResponseRedirect('/shop/cart')