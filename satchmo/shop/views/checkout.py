# Create your views here.

from django.shortcuts import render_to_response
from django import http
from django.template import RequestContext, Context
from django.template import loader
from satchmo.product.models import Item, Category, OptionItem
from satchmo.shop.models import Cart, CartItem, Config
from satchmo.contact.models import Contact
from sets import Set
from django.conf import settings
from django.contrib.auth import logout, login, authenticate
from django import forms
from django.core import validators
from django.contrib.auth.models import User
from satchmo.G11n.models import Country
from satchmo.discount.models import Discount

selection = "Please Select"

class GeographySelectField(forms.SelectField):
    #This field is used to override the error that's thrown if a selection is not in the list
    #Otherwise, the error looks very messy
    def isValidChoice(self, data, form):
        str_data = str(data)
        str_choices = [str(item[0]) for item in self.choices]
        if (str_data not in str_choices) and (str_data != selection):
            raise validators.ValidationError, gettext("Select a valid choice;")


class CheckoutManipulator(forms.Manipulator):
    def __init__(self, request, iso2="US"):
        self.country = Country.objects.get(iso2_code=iso2)
        areas = [(selection,selection)]
        for area in self.country.area_set.all():
            value_to_choose = (area.name,area.name)
            areas.append(value_to_choose)
        countries = [(self.country.iso2_code, self.country.name)]
        for country in Country.objects.filter(display=True):
            country_to_choose = (country.iso2_code, country.name)
            countries.append(country_to_choose)
        self.fields = (
            forms.EmailField(field_name="email", length=30, is_required=True),
            forms.TextField(field_name="first_name",length=30, is_required=True),
            forms.TextField(field_name="last_name",length=30, is_required=True),
            forms.TextField(field_name="phone",length=30, is_required=True),
            forms.TextField(field_name="street1",length=30, is_required=True),
            forms.TextField(field_name="street2",length=30, is_required=True),
            forms.TextField(field_name="city",length=30, is_required=True),
            GeographySelectField(field_name="state", is_required=True, choices=areas, validator_list=[self.isValidArea]),
            GeographySelectField(field_name="country", is_required=True, choices=countries),
            forms.TextField(field_name="zip",length=5, is_required=True),
            forms.CheckboxField(field_name="copyaddress"),
            forms.TextField(field_name="ship_street1",length=30),
            forms.TextField(field_name="ship_street2",length=30),
            forms.TextField(field_name="ship_city",length=30),
            GeographySelectField(field_name="ship_state", choices=areas, validator_list=[self.isValidArea]),
            forms.TextField(field_name="ship_zip",length=5),
            forms.TextField(field_name="discount",length=30, validator_list=[self.isValidDiscount])
        )
    
    def isValidArea(self, field_data, all_data):
        if (field_data == selection):
            raise validators.ValidationError("Please choose your %s." % self.country.get_adm_area_display())    
    
    def isValidDiscount(self, field_data, all_data):
        discount = Discount.objects.filter(code=field_data).filter(active=True)
        if discount.count() == 0:
            raise validators.ValidationError("Invalid discount")
        valid, msg = discount[0].isValid()
        if not valid:
            raise validators.ValidationError(msg)
        # todo: validate that it can work with these products
    
    def save(self, data):
        user_name = data['user_name']
        first_name = data['first_name']
        last_name = data['last_name']

def bill_ship(request):
    #First verify that the cart exists and has items
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            return render_to_response('checkout_empty_cart.html',RequestContext(request))
    if request.GET.get('iso2', False):
        iso2 = request.GET['iso2']
    else:
        iso2 = 'US'
    country = Country.objects.get(iso2_code=iso2)
    manipulator = CheckoutManipulator(request, iso2)
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            data = request.POST.copy()
            #manipulator.save(data)
            return http.HttpResponseRedirect('%s/' % (settings.SHOP_BASE))
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('checkout_form.html', {'form': form, 'country':country},
                                RequestContext(request))

    