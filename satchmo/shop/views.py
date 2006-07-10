# Create your views here.

from django.shortcuts import render_to_response
from satchmo.product.models import Item

def index(request):
    featured_items = Item.objects.filter(active="1").filter(featured="1")
    return render_to_response('base_index.html', {'all_items': featured_items})

def product(request, slug):
    item = Item.objects.filter(active="1").filter(short_name=slug)[0]
    return render_to_response('base_product.html',{'item':item})