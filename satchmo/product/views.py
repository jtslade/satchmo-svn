from satchmo.product.models import Item, Category
from django import http

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q

from satchmo.shop.templatetags.currency_filter import moneyfmt

from sets import Set

def get_price(request, slug):
    chosenOptions = Set()

    quantity = 1

    item = Item.objects.filter(active='1', short_name=slug)[0]

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

