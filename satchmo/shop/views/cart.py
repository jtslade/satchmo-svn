from django.core import urlresolvers
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.simplejson.encoder import JSONEncoder
from django.utils.translation import ugettext as _
from satchmo.product.models import Product
from satchmo.product.views import optionset_from_post
from satchmo.shop.models import Cart, CartItem
from satchmo.shop.views.utils import bad_or_missing

class NullCartItem(object):
    def __init__(self, itemid):
        self.id = itemid
        self.quantity = 0
        self.line_total = 0

def _set_quantity(request, force_delete=False):
    """Set the quantity for a specific cartitem.
    Checks to make sure the item is actually in the user's cart.
    """
    cart = None
    cartitem = None
    if request.session.get('cart'):
        cart = Cart.objects.get(id=request.session['cart'])
    else:
        return (False, None, None, _("No cart to update."))

    if force_delete:
        qty = 0
    else:
        try:
            qty = int(request.POST.get('quantity'))
        except (TypeError, ValueError):
            return (False, cart, None, _("Bad quantity."))
        if qty < 0:
            qty = 0

    try:
        itemid = int(request.POST.get('cartitem'))
    except (TypeError, ValueError):
        return (False, cart, None, _("Bad item number."))

    try:
        cartitem = CartItem.objects.get(pk=itemid, cart=cart)
    except CartItem.DoesNotExist:
        return (False, cart, None, _("No such item in your cart."))

    if qty == 0:
        cartitem.delete()
        cartitem = NullCartItem(itemid)
    else:
        cartitem.quantity = qty
        cartitem.save()

    return (True, cart, cartitem, "")

def display(request, cart = None, error_message = ""):
    """Display the items in the cart."""
    if (not cart) and request.session.get('cart'):
        cart = Cart.objects.get(id=request.session['cart'])

    context = RequestContext(request, {
        'cart': cart,
        'error_message': error_message
        })
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
        data['name'] = product.name

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

def remove(request):
    """Remove an item from the cart."""
    success, cart, cartitem, errors = _set_quantity(request, force_delete=True)
    if errors:
        return display(request, cart=cart, error_message=errors)
    else:
        url = urlresolvers.reverse('satchmo_cart')
        return HttpResponseRedirect(url)

def remove_ajax(request, template="json.html"):
    """Remove an item from the cart. Returning JSON formatted results."""
    data = {}
    if not request.POST:
        data['results'] = False
        data['errors'] = _('Internal error: please submit as a POST')

    else:
        success, cart, cartitem, errors = _set_quantity(request, force_delete=True)

        data['results'] = success
        data['errors'] = errors

        # note we have to convert Decimals to strings, since simplejson doesn't know about Decimals
        if cart and cartitem:
            data['cart_total'] = str(cart.total)
            data['cart_count'] = cart.numItems
            data['item_id'] = cartitem.id

        return render_to_response(template, {'json': JSONEncoder().encode(data)})

def set_quantity(request):
    """Set the quantity for a cart item.

    Intended to be called via the cart itself, returning to the cart after done.
    """
    if not request.POST:
        url = urlresolvers.reverse('satchmo_cart')
        return HttpResponseRedirect(url)

    success, cart, cartitem, errors = _set_quantity(request)
    return display(request, cart = cart, error_message = errors)

def set_quantity_ajax(request, template="json.html"):
    """Set the quantity for a cart item, returning results formatted for handling by script.
    """
    data = {}
    if not request.POST:
        data['results'] = False
        data['errors'] = _('Internal error: please submit as a POST')

    else:
        success, cart, cartitem, errors = _set_quantity(request)

        data['results'] = success
        data['errors'] = errors

        # note we have to convert Decimals to strings, since simplejson doesn't know about Decimals
        if cart and cartitem:
            data['cart_total'] = str(cart.total)
            data['cart_count'] = cart.numItems
            data['item_id'] = cartitem.id
            data['item_qty'] = cartitem.quantity
            data['item_price'] = str(cartitem.line_total)

    return render_to_response(template, {'json': JSONEncoder().encode(data)})

