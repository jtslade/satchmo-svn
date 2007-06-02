from sets import Set
from django import http
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.utils.translation import gettext as _
from satchmo.shop.templatetags.currency_filter import moneyfmt
from satchmo.product.models import Item, SubItem, Category
from satchmo.shop.views.utils import bad_or_missing


def get_options(item, selected_options=Set()):
    """
    Return a list of optiongroups and options for display to the customer.
    Only returns options that are used by subitems of this item.

    Return Value:
    [
    {
    name: 'group name',
    id: 'group id',
    items: [{ 
        name: 'opt name',
        value: 'opt value',
        price_change: 'opt price',
        selected: False,
        },{..}]
    },
    {..}
    }

    Note: This doesn't handle the case where you have multiple options and
    some combinations aren't available. For example, you have option_groups
    color and size, and you have a yellow/large, a yellow/small, and a
    white/small, but you have no white/large - the customer will still see
    the options white and large.
    """
    d = {}
    for subitem in item.subitem_set.all():
        for option in subitem.options.all():
            if not d.has_key(option.optionGroup_id):
                d[option.optionGroup.id] = {
                        'name': option.optionGroup.name,
                        'id': option.optionGroup.id,
                        'items': []
                        }
            if not option in d[option.optionGroup_id]['items']:
                d[option.optionGroup_id]['items'] += [option]
                option.selected = option.combined_id in selected_options
    return d.values()

def get_item(request, slug, subitemId=None):
    try:
        item = Item.objects.filter(active=True).filter(short_name=slug)[0]
    except IndexError:
        return bad_or_missing(request, _('The product you have requested does not exist.'))

    options = []
    if subitemId:
        subitem = SubItem.objects.filter(id=subitemId)[0]
        options = get_options(item, subitem.option_values)
    else:
        options = get_options(item)
    return render_to_response('base_product.html', {'item': item, 'options': options}, RequestContext(request))

def get_price(request, slug):
    chosenOptions = Set()
    quantity = 1
    
    try:
        item = Item.objects.filter(active=True, short_name=slug)[0]
    except IndexError:
        return http.HttpResponseNotFound(_('The product you have requested does not exist.'), mimetype='text/plain')

    for option in item.option_group.all():
        if request.POST.has_key(str(option.id)):
            chosenOptions.add('%s-%s' % (option.id, request.POST[str(option.id)]))

    if request.POST.has_key('quantity'):
        quantity = int(request.POST['quantity'])

    chosenItem = item.get_sub_item(chosenOptions)

    if not chosenItem:
        return http.HttpResponse('not available', mimetype="text/plain")

    price = moneyfmt(chosenItem.get_qty_price(quantity))

    return http.HttpResponse(price, mimetype="text/plain")


def do_search(request):
    keywords = request.POST['keywords'].split(' ')
    categories = Category.objects
    items = Item.objects.filter(active=True)
    for keyword in keywords:
        if not keyword:
            continue

        categories = categories.filter(Q(name__icontains=keyword) | Q(meta__icontains=keyword) | Q(description__icontains=keyword))
        items = items.filter(Q(verbose_name__icontains=keyword) | Q(description__icontains=keyword) | Q(meta__icontains=keyword))
    list = []
    for category in categories:
        list.append(('Category', category.name, category.get_absolute_url()))
    for item in items:
        list.append(('Item', item.verbose_name, item.get_absolute_url()))

    return render_to_response('search.html', {'results': list}, RequestContext(request))

