# Create your views here.

from django.shortcuts import render_to_response
from django import http
from django.template import RequestContext, Context
from django.template import loader
from satchmo.product.models import Item, Category, OptionItem
from satchmo.shop.models import Cart, CartItem, Config
from satchmo.contact.models import Contact, AddressBook, PhoneNumber
from sets import Set
from django.conf import settings
from django.contrib.auth import logout, login, authenticate
from django import forms
from django.core import validators
from django.contrib.auth.models import User
from satchmo.G11n.models import Country
from satchmo.discount.models import Discount
from datetime import date
import calendar
from satchmo.shop.views.utils import CreditCard
from satchmo.shipping.modules import *

selection = "Please Select"
credit_types = (
                ('Visa','Visa'),
                ('Mastercard','Mastercard'),
                ('Discover','Discover'),
                )

class GeographySelectField(forms.SelectField):
    #This field is used to override the error that's thrown if a selection is not in the list
    #Otherwise, the error looks very messy
    def isValidChoice(self, data, form):
        str_data = str(data)
        str_choices = [str(item[0]) for item in self.choices]
        if (str_data not in str_choices) and (str_data != selection):
            raise validators.ValidationError, gettext("Select a valid choice;")


class ContactInfoManipulator(forms.Manipulator):
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
            forms.TextField(field_name="street2",length=30),
            forms.TextField(field_name="city",length=30, is_required=True),
            GeographySelectField(field_name="state", is_required=True, choices=areas, validator_list=[self.isValidArea]),
            GeographySelectField(field_name="country", is_required=True, choices=countries),
            forms.TextField(field_name="zip_code",length=5, is_required=True),
            forms.CheckboxField(field_name="copyaddress"),
            forms.TextField(field_name="ship_street1",length=30),
            forms.TextField(field_name="ship_street2",length=30),
            forms.TextField(field_name="ship_city",length=30),
            GeographySelectField(field_name="ship_state", choices=areas, validator_list=[self.isValidArea]),
            forms.TextField(field_name="ship_zip_code",length=5),
        )
    
    def isValidArea(self, field_data, all_data):
        if (field_data == selection):
            raise validators.ValidationError("Please choose your %s." % self.country.get_adm_area_display())    
       
    def save(self, data):
        #Check to see if contact exists
        #If not, create a contact and copy in the address and phone number
        newCustomer = Contact()
        for field in newCustomer.__dict__.keys():
            if data.has_key(field):
                newCustomer.__setattr__(field,data[field])
        newCustomer.role = "Customer"
        newCustomer.save()
        address = AddressBook()
        for field in address.__dict__.keys():
            if data.has_key(field):
                address.__setattr__(field,data[field])
        address.contact = newCustomer
        address.is_default_billing = True
        address.save()
        newCustomer.save()
        if data.has_key('copyaddress'):
            address.is_default_shipping = True
        else:
            ship_address = AddressBook()
            for field in address.__dict__.keys():
                if data.has_key('ship_'+field):
                    ship_address.__setattr__(field,data['ship_'+field])
            ship_address.is_default_shipping = True
            ship_address.contact = newCustomer
            ship_address.save()
        phone = PhoneNumber()
        phone.primary = True
        phone.phone = data['phone']
        phone.contact = newCustomer
        phone.save()
        return(newCustomer.id)

class payShipManipulator(forms.Manipulator):
    def __init__(self, request):
        year_now = date.today().year

        shipping_options = []
        for module in activeModules:
            shipping_module = eval(module)
            shipping_instance = shipping_module()
            shipping_options.append((shipping_instance.description(), shipping_instance.description()))
        self.fields = (
            forms.SelectField(field_name="credit_type", choices=credit_types,is_required=True),
            forms.TextField(field_name="credit_number",length=20, is_required=True, validator_list=[self.isCardValid]),
            forms.SelectField(field_name="month_expires",choices=[(month,month) for month in range(1,13)], is_required=True),
            forms.SelectField(field_name="year_expires",choices=[(year,year) for year in range(year_now,year_now+5)], is_required=True,  
                                                        validator_list=[self.isCardExpired]),
            forms.TextField(field_name="ccv", length=4, is_required=True),
            forms.RadioSelectField(field_name="shipping",choices=shipping_options),
            forms.TextField(field_name="discount",length=30, validator_list=[self.isValidDiscount]),
            )
            
    def isCardExpired(self,field_data,all_data):
        entered_year = int(all_data["year_expires"])
        entered_month = int(all_data["month_expires"])
        max_day = calendar.monthrange(entered_year,entered_month)[1]
        if date.today() > date(year=entered_year, month=entered_month,day=max_day):
            raise validators.ValidationError("Your card has expired.")
    
    def isCardValid(self, field_data, all_data):
        card = CreditCard(all_data["credit_number"], all_data["ccv"], all_data["credit_type"])
        results, msg = card.verifyCardTypeandNumber()
        if not results:
            raise validators.ValidationError(msg)
    
    def isValidDiscount(self, field_data, all_data):
        discount = Discount.objects.filter(code=field_data).filter(active=True)
        if discount.count() == 0:
            raise validators.ValidationError("Invalid discount")
        valid, msg = discount[0].isValid()
        if not valid:
            raise validators.ValidationError(msg)
        # todo: validate that it can work with these products   
        
def contact_info(request):
    #First verify that the cart exists and has items
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            return render_to_response('checkout_empty_cart.html',RequestContext(request))
    else:
        return render_to_response('checkout_empty_cart.html',RequestContext(request))
    if request.GET.get('iso2', False):
        iso2 = request.GET['iso2']
    else:
        iso2 = 'US'
    country = Country.objects.get(iso2_code=iso2)
    manipulator = ContactInfoManipulator(request, iso2)
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            data = request.POST.copy()
            custID = manipulator.save(data)
            request.session['custID'] = custID
            print custID
            return http.HttpResponseRedirect('%s/checkout/pay/' % (settings.SHOP_BASE))
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('checkout_form.html', {'form': form, 'country':country},
                                RequestContext(request))

def pay_ship(request):
    #First verify that the customer exists
    if not request.session.get('custID', False):
        return http.HttpResponseRedirect('%s/checkout' % (settings.SHOP_BASE))
    #Verify we still have items in the cart
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            return render_to_response('checkout_empty_cart.html',RequestContext(request))
    else:
        return render_to_response('checkout_empty_cart.html',RequestContext(request))    
    #Verify order info is here
    manipulator = payShipManipulator(request)
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            data = request.POST.copy()
            #manipulator.save(data)
            return http.HttpResponseRedirect('%s/confirm' % (settings.SHOP_BASE))
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('checkout_pay_ship.html', {'form': form},
                                RequestContext(request))    