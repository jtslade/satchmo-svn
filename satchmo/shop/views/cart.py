from django.shortcuts import render_to_response
from django import http
from django.utils.simplejson.encoder import JSONEncoder
from satchmo.shop.models import Cart, CartItem, Config
from satchmo.product.models import Product, ConfigurableProduct, Category, Option
from satchmo.product.views import optionset_from_post
from sets import Set
from django.template import RequestContext, Context
from django.conf import settings
from satchmo.shop.views.utils import bad_or_missing
from decimal import Decimal

def display(request):
    #Show the items in the cart
    cart_list = []
    total = Decimal("0")
    all_items = []
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        total = tempCart.total
        all_items = tempCart.cartitem_set.all()
    return render_to_response('base_cart.html', {'all_items' : all_items,
                                                 'total':total},
                                                 RequestContext(request))

def add(request, id=0):
    #Todo: Error checking for invalid combos
    #Add an item to the session/cart

    try:
        product = Product.objects.get(slug=request.POST['productname'])
        if 'ConfigurableProduct' in product.get_subtypes():
            #This can happen if ajax isn't working to update productname
            cp = product.configurableproduct
            chosenOptions = optionset_from_post(cp, request.POST)
            product = cp.get_product_from_options(chosenOptions)
    except Product.DoesNotExist:
        return bad_or_missing(request, 'The product you have requested does '
                'not exist.')
    try:
        quantity = int(request.POST['quantity'])
    except ValueError:
        return render_to_response('base_product.html', {
            'item': product,
            'error_message': "Please enter a whole number"},
             RequestContext(request))
    if quantity < 0:
        return render_to_response('base_product.html', {
            'item': product,
            'error_message': "Negative numbers can not be entered"},
             RequestContext(request))

    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
    else:
        tempCart = Cart()
    tempCart.save() #need to make sure there's an id
    tempCart.add_item(product, number_added=quantity)
    request.session['cart'] = tempCart.id

    return http.HttpResponseRedirect('%s/cart/' % (settings.SHOP_BASE))

def add_ajax(request, id=0, template="json.html"):
    data = {'errors': []}
    try:
        product = Product.objects.get(slug=request.POST['productname'])
        if 'ConfigurableProduct' in product.get_subtypes():
            #This can happen if ajax isn't working to update productname
            cp = product.configurableproduct
            chosenOptions = optionset_from_post(cp, request.POST)
            product = cp.get_product_from_options(chosenOptions)

        data['id'] = product.id
        data['name'] = product.full_name

        try:
            quantity = int(request.POST['quantity'])
            if quantity < 0:
                data['errors'].append(['quantity',_('Choose a quantity')])
            
        except ValueError:
            data['errors'].append(['quantity',_('Choose a whole number')])
            
    except Product.DoesNotExist:
        data['errors'].append(['product', _('The product you have requested does not exist.')])
        
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
    else:
        tempCart = Cart()
        
    if len(data['errors']) == 0:    
        tempCart.save() #need to make sure there's an id
        tempCart.add_item(product, number_added=quantity)
        request.session['cart'] = tempCart.id
        data['results'] = _('Success')
    else:
        data['results'] = _('Error')
        
    data['cart_count'] = tempCart.numItems

    return render_to_response(template, {'json' : JSONEncoder().encode(data)})
    
def remove(request, id):
    tempCart = Cart.objects.get(id=request.session['cart'])
    quantity = int(request.POST.get('quantity','999999'))
    tempCart.remove_item(id, quantity)
    return http.HttpResponseRedirect('%s/cart/' % (settings.SHOP_BASE))
