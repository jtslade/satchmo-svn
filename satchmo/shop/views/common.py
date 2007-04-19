"""
Common code used for the checkout process
"""
from django import newforms as forms
from satchmo.contact.models import Contact, AddressBook, PhoneNumber

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


def save_contact_info(data, contact=None):
    #Save the contact info into the database
    #Check to see if contact exists
    #If not, create a contact and copy in the address and phone number
    if not contact:
        customer = Contact()
    else:
        customer = contact
    for field in customer.__dict__.keys():
        try:
            setattr(customer, field, data[field])
        except KeyError:
            pass
    customer.role = "Customer"
    customer.save()
    address = AddressBook()
    address_keys = address.__dict__.keys()
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
        print "Entering"
        ship_address = AddressBook()
        for field in address_keys:
            try:
                setattr(ship_address, field, data['ship_' + field])
            except KeyError:
                pass
        ship_address.is_default_shipping = True
        ship_address.is_default_billing = False
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
