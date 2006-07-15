import os, sys
import django.core.management, django.core
from os.path import isdir, isfile, join, dirname

os.environ["DJANGO_SETTINGS_MODULE"]="satchmo.settings"

from satchmo.customer.models import *
from satchmo.product.models import * 
from satchmo.supplier.models import *

def find_site(): 
    """Find the site by looking at the environment."""
    try: 
        settings_module = os.environ['DJANGO_SETTINGS_MODULE']
    except KeyError: 
        raise AssertionError, "DJANGO_SETTINGS_MODULE not set."

    settingsl = settings_module.split('.')
    site = __import__(settingsl[0])
    settings = __import__(settings_module, {}, {}, settingsl[-1])
    return site, settings

def delete_db(settings): 
    """Delete the old database."""
    engine = settings.DATABASE_ENGINE
    if engine == 'sqlite3': 
        try: 
            os.unlink(settings.DATABASE_NAME)
        except OSError: 
            pass
    elif engine == 'mysql': 
        import _mysql
        s = _mysql.connect(host=settings.DATABASE_HOST, 
                           user=settings.DATABASE_USER, 
                           passwd=settings.DATABASE_PASSWORD)
        for cmd in ['drop database if exists %s', 
                    'create database %s']: 
            s.query(cmd % settings.DATABASE_NAME)
    else: 
        raise AssertionError, "Unknown database engine %s", engine


def init_and_install():
    django.core.management.syncdb()
    
def load_data():
    # Import some customers
    c1 = Customer(first_name="Chris", last_name="Smith", phone="655-555-0164",
                  fax="900-100-9010", email="chris@aol.com", notes="Really cool stuff")
    c1.save()
    c2 = Customer(first_name="John", last_name="Smith", phone="901-555-9242",
                    fax="800-199-1000", email="abc@comcast.com", notes="Second user")
    c2.save()
    # Import some addresses for these customers
    a1 = AddressBook(description="Home", street1="8235 Pike Street", city="Anywhere Town", state="TN",
                 zip_code="38138", country="US", is_default_shipping=True, customer=c1)
    a1.save()
    a2 = AddressBook(description="Work", street1="1245 Main Street", city="Stillwater", state="MN",
                 zip_code="55082", country="US", is_default_shipping=True, customer=c2)
    a2.save()
    #Import some suppliers
    s1 = Supplier(name="Rhinestone Ronny", address1="918 Funky Town St", address2="Suite 200",
                  city="Fishkill", state="NJ", zip="19010", phone1="800-188-7611", fax="900-110-1909", email="ron@rhinestone.com",
                  notes="My main supplier")
    s1.save()

    s2 = Supplier(name="Shirt Sally", address1="9 ABC Lane", 
                  city="Happyville", state="MD", zip="190111", phone1="888-888-1111", fax="999-110-1909", email="sally@shirts.com",
                  notes="Shirt Supplier")
    s2.save()
    #Create 2 categories
    cat1 = Category(name="Shirt",slug="shirt",description="Women's Shirts")
    cat1.save()
    cat2 = Category(name="Short Sleeve",slug="shortsleeve",description="Short sleeve shirts", parent=cat1)
    cat2.save()
    
    #Create an item
    i1 = Item(verbose_name="Django Rocks shirt", short_name="DJ-Rocks", description="Really cool shirt", price="20.00", 
             active=True, featured=True, category=cat1)
    i1.save()
    i2 = Item(verbose_name="Python Rocks shirt", short_name="PY-Rocks", description="Really cool python shirt", price="19.50", 
             active=True, featured=True, category=cat2)
    i2.save()


    #Create an attribute set 
    optSet1 = OptionGroup(name="sizes", sort_order=1)
    optSet2 = OptionGroup(name="colors", sort_order=2)
    optSet1.save()
    optSet2.save()

    optItem1a = OptionItem(name="Small", value="S", displayOrder=1, optionGroup=optSet1)
    optItem1a.save()
    optItem1b = OptionItem(name="Medium", value="M", displayOrder=2, optionGroup=optSet1)
    optItem1b.save()
    optItem1c = OptionItem(name="Large", value="L", displayOrder=3, optionGroup=optSet1)
    optItem1c.save()

    optItem2a = OptionItem(name="Black", value="B", displayOrder=1, optionGroup=optSet2)
    optItem2a.save()
    optItem2b = OptionItem(name="White", value="W", displayOrder=2, optionGroup=optSet2)
    optItem2b.save()
    optItem2c = OptionItem(name="Blue", value="BL", displayOrder=3, optionGroup=optSet2)
    optItem2c.save()

    #Add the option group to our items
    i1.option_group.add(optSet1)
    i1.save()
    i1.option_group.add(optSet2)
    i1.save()
    i2.option_group.add(optSet1)
    i2.save()


def main(): 
    """Flush it all, baby!"""
    try: 
        site, settings = find_site()
        delete_db(settings)
        init_and_install()
        load_data()
    except AssertionError, ex: 
        print ex.args[0]
        
if __name__ == '__main__': 
    main()

   

