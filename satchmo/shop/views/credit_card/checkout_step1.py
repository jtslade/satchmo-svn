####################################################################
# First step in the order process - capture all the demographic info
#####################################################################

from django.shortcuts import render_to_response
from django import http
from django.template import RequestContext, Context
from django.template import loader
from satchmo.product.models import Item, Category, OptionItem
from satchmo.shop.models import Cart, CartItem, Config
from satchmo.contact.models import Contact, AddressBook, PhoneNumber
from django.conf import settings
from django import newforms as forms
from satchmo.i18n.models import Country

selection = "Please Select"


class ContactInfoForm(forms.Form):
    email = forms.EmailField(max_length=30)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    phone = forms.CharField(max_length=30)
    street1 = forms.CharField(max_length=30)
    street2 = forms.CharField(max_length=30, required=False)
    city = forms.CharField(max_length=30)
    state = forms.ChoiceField(initial=selection)
    country = forms.ChoiceField()
    postalCode = forms.CharField(max_length=5)
    copy_address = forms.BooleanField(required=False)
    ship_street1 = forms.CharField(max_length=30, required=False)
    ship_street2 = forms.CharField(max_length=30, required=False)
    ship_city = forms.CharField(max_length=30, required=False)
    ship_state = forms.ChoiceField(initial=selection, required=False)
    ship_postalCode = forms.CharField(max_length=5, required=False)
    
    def __init__(self, countries, areas, *args, **kwargs):
        super(ContactInfoForm, self).__init__(*args, **kwargs)
        self.fields['country'].choices = countries
        self.fields['state'].choices = areas
        self.fields['ship_state'].choices = areas
    
    """
    clean_* methods are called in same order as the form's fields.
    self.clean_data will have data for each of the previous fields and the
    field currently being cleaned.
    For details, see django.newforms.BaseForm.full_clean()
    """
    
    def clean_state(self):
        data = self.clean_data['state']
        if data == selection:
            raise forms.ValidationError('This field is required.')
        return data

    def clean_ship_state(self):
        if self.clean_data['copy_address']:
            if 'state' in self.clean_data:
                self.clean_data['ship_state'] = self.clean_data['state']
            return self.clean_data['ship_state']
        data = self.clean_data['ship_state']
        if data == selection:
            raise forms.ValidationError('This field is required.')
        return data
    
    def ship_charfield_clean(self, field_name):
        if self.clean_data['copy_address']:
            if field_name in self.clean_data:
                self.clean_data['ship_' + field_name] = self.clean_data[field_name]
            return self.clean_data['ship_' + field_name]
        field = forms.CharField(max_length=30)
        return field.clean(self.clean_data['ship_' + field_name])
    
    def clean_ship_street1(self):
        return self.ship_charfield_clean('street1')
    
    def clean_ship_street2(self):
        if self.clean_data['copy_address']:
            if 'street2' in self.clean_data:
                self.clean_data['ship_street2'] = self.clean_data['street2']
        return self.clean_data['ship_street2']
    
    def clean_ship_city(self):
        return self.ship_charfield_clean('city')

    def clean_ship_postalCode(self):
        return self.ship_charfield_clean('postalCode')


def contact_info(request):
    #First verify that the cart exists and has items
    if request.session.get('cart', False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            return render_to_response('checkout_empty_cart.html', RequestContext(request))
    else:
        return render_to_response('checkout_empty_cart.html', RequestContext(request))

    # Get the default country
    if request.GET.get('iso2', False):
        iso2 = request.GET['iso2']
    else:
        iso2 = 'US'
    default_country = Country.objects.get(iso2_code=iso2)
    init_data = {'country': default_country.iso2_code}
    # Create country and state lists
    areas = [(selection,selection)]
    for area in default_country.area_set.all():
        value_to_choose = (area.abbrev, area.name)
        areas.append(value_to_choose)
    countries = [(default_country.iso2_code, default_country.name)]
    for country in Country.objects.filter(display=True):
        country_to_choose = (country.iso2_code, country.name)
        #Make sure the default only shows up once
        if country.iso2_code <> default_country.iso2_code:
            countries.append(country_to_choose)
    
    if request.session.get('custID', False):
        contact = Contact.objects.get(id=request.session['custID'])
    else:
        contact = None
    
    if request.POST:
        new_data = request.POST.copy()
        form = ContactInfoForm(countries, areas, new_data, initial=init_data)
        
        if form.is_valid():
            if not contact:
                custID = save(form.clean_data)
                request.session['custID'] = custID
            else:
                custID = save(form.clean_data, contact)
            #TODO - Create an order here and associate it with a session
            return http.HttpResponseRedirect('%s/checkout/pay/' % (settings.SHOP_BASE))
    else:
        if contact:
            #If a person has their contact info, make sure we populate it in the form
            for item in contact.__dict__.keys():
                init_data[item] = getattr(contact,item)
            for item in contact.shipping_address.__dict__.keys():
                init_data["ship_"+item] = getattr(contact.shipping_address,item)
            for item in contact.billing_address.__dict__.keys():
                init_data[item] = getattr(contact.billing_address,item)
            init_data['phone'] = contact.primary_phone.phone
        form = ContactInfoForm(countries, areas, initial=init_data)
    
    return render_to_response('checkout_form.html', {'form': form, 'country': default_country}, RequestContext(request))


def save(data, contact=None):
    #Check to see if contact exists
    #If not, create a contact and copy in the address and phone number
    if not contact:
        customer = Contact()
    else:
        customer = contact
    for field in customer.__dict__.iterkeys():
        try:
            setattr(customer, field, data[field])
        except KeyError:
            pass
    customer.role = "Customer"
    customer.save()
    address = AddressBook()
    address_keys = address.__dict__.iterkeys()
    for field in address_keys:
        try:
            setattr(address, field, data[field])
        except KeyError:
            pass
    address.contact = customer
    address.is_default_billing = True
    address.is_default_shipping = data['copy_address']
    address.save()
    if not data['copy_address']:
        ship_address = AddressBook()
        for field in address_keys:
            try:
                setattr(ship_address, field, data['ship_' + field])
            except KeyError:
                pass
        ship_address.is_default_shipping = True
        ship_address.contact = customer
        ship_address.save()
    if not customer.primary_phone:
        phone = PhoneNumber()
        phone.primary = True
    else:
        phone = customer.primary_phone
    phone.phone = data['phone']
    phone.contact = customer
    phone.save()        
    return customer.id
