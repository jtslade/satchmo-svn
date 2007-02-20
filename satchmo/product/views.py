from django.core import serializers
from satchmo.product.models import Item
from django import http

from satchmo.shop.templatetags.currency_filter import moneyfmt

from sets import Set

def get_json(request, slug):
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



