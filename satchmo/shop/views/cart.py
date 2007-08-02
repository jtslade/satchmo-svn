from decimal import Decimal
from sets import Set
from django.conf import settings
from django.core import urlresolvers
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext, Context
from django.utils.simplejson.encoder import JSONEncoder
from django.utils.translation import ugettext as _
from satchmo.shop.views.utils import bad_or_missing
from satchmo.shop.models import Cart, CartItem, Config
from satchmo.product.models import Product, ConfigurableProduct, Category, Option
from satchmo.product.views import optionset_from_post

def display(request):
    """Display the items in the cart."""
    total = Decimal("0")
    all_items = []
    if request.session.get('cart'):
        cart = Cart.objects.get(id=request.session['cart'])
        total = cart.total
        all_items = cart.cartitem_set.all()
    context = RequestContext(request, {
        'all_items': all_items, 'total': total})
    return render_to_response('base_cart.html', context)

def add(request, id=0):
    """Add an item to the cart."""
    #TODO: Error checking for invalid combos

    try:
        product = Product.objects.get(slug=request.POST['productname'])
        if 'ConfigurableProduct' in product.get_subtypes():
            # This happens when productname cannot be updated by javascript.
            cp = product.configurableproduct
            chosenOptions = optionset_from_post(cp, request.POST)
            product = cp.get_product_from_options(chosenOptions)
    except Product.DoesNotExist:
        return bad_or_missing(request, _('The product you have requested does not exist.'))
    try:
        quantity = int(request.POST['quantity'])
    except ValueError:
        context = RequestContext(request, {
            'product': product,
            'error_message': _("Please enter a whole number.")})
        return render_to_response('base_product.html', context)
    if quantity < 1:
        context = RequestContext(request, {
            'product': product,
            'error_message': _("Please enter a positive number.")})
        return render_to_response('base_product.html', context)

    if request.session.get('cart'):
        cart = Cart.objects.get(id=request.session['cart'])
    else:
        cart = Cart()
        cart.save() # Give the cart an id
    cart.add_item(product, number_added=quantity)
    request.session['cart'] = cart.id

    url = urlresolvers.reverse('satchmo_cart')
    return HttpResponseRedirect(url)

def add_ajax(request, id=0, template="json.html"):
    data = {'errors': []}
    try:
        product = Product.objects.get(slug=request.POST['productname'])
        if 'ConfigurableProduct' in product.get_subtypes():
            # This happens when productname cannot be updated by javascript.
            cp = product.configurableproduct
            chosenOptions = optionset_from_post(cp, request.POST)
            product = cp.get_product_from_options(chosenOptions)

        data['id'] = product.id
        data['name'] = product.full_name

        try:
            quantity = int(request.POST['quantity'])
            if quantity < 0:
                data['errors'].append(('quantity', _('Choose a quantity.')))

        except ValueError:
            data['errors'].append(('quantity', _('Choose a whole number.')))

    except Product.DoesNotExist:
        data['errors'].append(('product', _('The product you have requested does not exist.')))

    if request.session.get('cart'):
        tempCart = Cart.objects.get(id=request.session['cart'])
    else:
        tempCart = Cart()
        tempCart.save() # Give the cart an id

    if not data['errors']:
        tempCart.add_item(product, number_added=quantity)
        request.session['cart'] = tempCart.id
        data['results'] = _('Success')
    else:
        data['results'] = _('Error')

    data['cart_count'] = tempCart.numItems

    return render_to_response(template, {'json' : JSONEncoder().encode(data)})

def remove(request, id):
    """Remove an item from the cart."""
    item = CartItem.objects.get(id=id)
    item.delete()

    url = urlresolvers.reverse('satchmo_cart')
    return HttpResponseRedirect(url)

