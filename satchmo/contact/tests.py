r"""
>>> import datetime
>>> from satchmo.contact.models import *

# Create a contact

>>> contact1 = Contact.objects.create(first_name="Jim", last_name="Tester", 
... role="Customer", email="Jim@JimWorld.com")
>>> contact1.full_name
'Jim Tester'
>>> contact1
<Contact: Jim Tester>

# Add a phone number for this person
>>> phone1 = PhoneNumber.objects.create(contact=contact1,type='Home', phone="800-111-9900", primary=True)
>>> contact1.primary_phone
<PhoneNumber: Home - 800-111-9900>

# Make sure we can only have one primary phone number
>>> phone2 = PhoneNumber.objects.create(contact=contact1,type='Work', phone="800-111-9901", primary=True)
Traceback (most recent call last):
    ...
IntegrityError: (1062, "Duplicate entry '1-1' for key 2")

#Add an address & make sure it is default billing and shipping

>>> add1 = AddressBook.objects.create(contact=contact1, description="Home Address",
... street1="56 Cool Lane", city="Niftyville", state="IA", postalCode="12344",
... country="USA")
>>> contact1.billing_address
<AddressBook: Jim Tester - Home Address>
>>> contact1.shipping_address
<AddressBook: Jim Tester - Home Address>
>>> contact1.shipping_address.street1
'56 Cool Lane'
>>> contact1.shipping_address.street2
''
>>> contact1.billing_address.street1
'56 Cool Lane'
>>> contact1.billing_address.street2
''

#Add a new shipping address
>>> add2 = AddressBook(description="Work Address", street1="56 Industry Way", city="Niftytown", 
... state="IA", postalCode="12366", country="USA", is_default_shipping=True)
>>> add2.contact = contact1
>>> add2.save()
>>> contact1.save()
>>> contact1.billing_address
<AddressBook: Jim Tester - Home Address>
>>> contact1.shipping_address
<AddressBook: Jim Tester - Work Address>

#Need to add some more checks here
"""

if __name__ == "__main__":
    import doctest
    doctest.testmod()