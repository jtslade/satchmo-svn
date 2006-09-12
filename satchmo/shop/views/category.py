from django.shortcuts import render_to_response
from django import http
from satchmo.product.models import Category
from django.template import RequestContext, Context
from satchmo.shop.views.utils import bad_or_missing

def root(request, slug):
    #Display the category page if we're not dealing with a child category
    try:
        category = Category.objects.filter(slug=slug)[0]
    except IndexError:
        return bad_or_missing(request, 'The category you have requested does '
            'not exist.')
    return render_to_response('base_category.html',{'category':category},
                                RequestContext(request))

def children(request, slug_parent, slug):
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
            
    return render_to_response('base_category.html',{'category':category}, 
                                RequestContext(request))
