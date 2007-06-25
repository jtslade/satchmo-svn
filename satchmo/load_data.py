#!/usr/bin/env python

import os, sys
import urllib
from os.path import isdir, isfile, join, dirname
import os
import string
import csv
import tarfile
import shutil
sys.path.insert(0, "django-src-here")
sys.path.insert(0, "satchmo-src-here")

if not os.environ.has_key("DJANGO_SETTINGS_MODULE"):
    from settings import DJANGO_SETTINGS_MODULE
    os.environ["DJANGO_SETTINGS_MODUlE"]=DJANGO_SETTINGS_MODULE

import django.core.management, django.core
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.auth.models import User


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
            
    elif engine in ('postgresql', 'postgresql_psycopg2'):

        if settings.DATABASE_NAME == '':
            raise AssertionError, "You must specified a value for DATABASE_NAME in local_settings.py."
        if settings.DATABASE_USER == '':
            raise AssertionError, "You must specified a value for DATABASE_USER in local_settings.py."
        params=" --username=%s  --password" % settings.DATABASE_USER
        if settings.DATABASE_HOST:
            params += " --host=%s" % settings.DATABASE_HOST
        if settings.DATABASE_PORT:
            params += " --port=%s" % settings.DATABASE_PORT
        params += " %s" % settings.DATABASE_NAME
        print """You will be prompted for the password for the user
        '%s' twice.  Once to drop an existing database and then a second time
        for create the database """ % settings.DATABASE_USER
        for cmd in ['dropdb %s', 'createdb %s']:
            os.system(cmd % params) 
    
    else: 
        raise AssertionError, "Unknown database engine %s", engine


def init_and_install():
    django.core.management.syncdb()
    
def load_data():
    from satchmo.contact.models import Contact, AddressBook, PhoneNumber
    from satchmo.product.models import Item, Category, OptionGroup, OptionItem, ItemImage 
    from satchmo.supplier.models import Organization
    from satchmo.shop.models import Config
    from django.conf import settings
    #Load basic configuration information
    print "Creating site..."
    site = Site.objects.get(id=settings.SITE_ID)
    site.domain = settings.SITE_DOMAIN  
    site.name = settings.SITE_NAME
    site.save()
    config = Config(site=site, storeName = settings.SITE_NAME, noStockCheckout=False)
    config.save()
    print "Creating Customers..."
    # Import some customers
    c1 = Contact(first_name="Chris", last_name="Smith", email="chris@aol.com", role="Customer", notes="Really cool stuff")
    c1.save()
    p1 = PhoneNumber(contact=c1, phone="601-555-5511", type="Home",primary=True)
    p1.save()
    c2 = Contact(first_name="John", last_name="Smith", email="abc@comcast.com", role="Customer", notes="Second user")
    c2.save()
    p2 = PhoneNumber(contact=c2, phone="999-555-5111", type="Work",primary=True)
    p2.save()
    # Import some addresses for these customers
    a1 = AddressBook(description="Home", street1="8235 Pike Street", city="Anywhere Town", state="TN",
                 postalCode="38138", country="US", is_default_shipping=True, contact=c1)
    a1.save()
    a2 = AddressBook(description="Work", street1="1245 Main Street", city="Stillwater", state="MN",
                 postalCode="55082", country="US", is_default_shipping=True, contact=c2)
    a2.save()
    print "Creating Suppliers..."
    #Import some suppliers
    org1 = Organization(name="Rhinestone Ronny", type="Company",role="Supplier")
    org1.save()
    c4 = Contact(first_name="Fred", last_name="Jones", email="fj@rr.com", role="Supplier", organization=org1)
    c4.save()
    p4 = PhoneNumber(contact=c4,phone="800-188-7611", type="Work", primary=True)
    p4.save()
    p5 = PhoneNumber(contact=c4,phone="755-555-1111",type="Fax")
    p5.save()
    a3 = AddressBook(contact=c4, description="Mailing address", street1="Receiving Dept", street2="918 Funky Town St", city="Fishkill",
                     state="NJ", postalCode="19010")
    a3.save()
    #s1 = Supplier(name="Rhinestone Ronny", address1="918 Funky Town St", address2="Suite 200",
    #              city="Fishkill", state="NJ", zip="19010", phone1="800-188-7611", fax="900-110-1909", email="ron@rhinestone.com",
    #              notes="My main supplier")
    #s1.save()

    #s2 = Supplier(name="Shirt Sally", address1="9 ABC Lane", 
    #    city="Happyville", state="MD", zip="190111", phone1="888-888-1111", fax="999-110-1909", email="sally@shirts.com",
    #              notes="Shirt Supplier")
    #s2.save()
    
    
    print "Creating Categories..."
    #Create some categories
    cat1 = Category(name="Shirts",slug="shirts",description="Women's Shirts")
    cat1.save()
    cat2 = Category(name="Short Sleeve",slug="shortsleeve",description="Short sleeve shirts", parent=cat1)
    cat2.save()
    cat3 = Category(name="Books",slug="book",description="Books")
    cat3.save()
    cat4 = Category(name="Fiction",slug="fiction",description="Fiction Books", parent=cat3)
    cat4.save()
    cat5 = Category(name="Science Fiction",slug="scifi",description="Science Fiction",parent=cat4)
    cat5.save()
    cat6 = Category(name="Non Fiction",slug="nonfiction",description="Non Fiction",parent=cat3)
    cat6.save()
    
    
    print "Creating items..."   
    #Create some items
    from decimal import Decimal
    p1 = Decimal("20.00")
    i1 = Item(verbose_name="Django Rocks shirt", short_name="DJ-Rocks", description="Really cool shirt", base_price=p1, 
             active=True, featured=True)
    i1.save()
    i1.category.add(cat1)
    i1.save()
    i2 = Item(verbose_name="Python Rocks shirt", short_name="PY-Rocks", description="Really cool python shirt", base_price="19.50", 
             active=True, featured=True)
    i2.save()
    i2.category.add(cat2)
    i2.save()
    i3 = Item(verbose_name="A really neat book", short_name="neat-book", description="A neat book.  You should buy it.", base_price="5.00", 
             active=True, featured=True)
    i3.save()
    i3.category.add(cat4)
    i3.save()
    i4 = Item(verbose_name="Robots Attack!", short_name="robot-attack", description="Robots try to take over the world.", base_price="7.99", 
             active=True, featured=True)
    i4.save()
    i4.category.add(cat5)
    i4.save()

    #Create an attribute set 
    optSet1 = OptionGroup(name="sizes", sort_order=1)
    optSet2 = OptionGroup(name="colors", sort_order=2)
    optSet1.save()
    optSet2.save()
    
    optSet3 = OptionGroup(name="Book type", sort_order=1)
    optSet3.save()
    
    optItem1a = OptionItem(name="Small", value="S", displayOrder=1, optionGroup=optSet1)
    optItem1a.save()
    optItem1b = OptionItem(name="Medium", value="M", displayOrder=2, optionGroup=optSet1)
    optItem1b.save()
    optItem1c = OptionItem(name="Large", value="L", displayOrder=3, price_change = 1.00, optionGroup=optSet1)
    optItem1c.save()

    optItem2a = OptionItem(name="Black", value="B", displayOrder=1, optionGroup=optSet2)
    optItem2a.save()
    optItem2b = OptionItem(name="White", value="W", displayOrder=2, optionGroup=optSet2)
    optItem2b.save()
    optItem2c = OptionItem(name="Blue", value="BL", displayOrder=3, price_change=2.00, optionGroup=optSet2)
    optItem2c.save()

    optItem3a = OptionItem(name="Hard cover", value="hard", displayOrder=1, optionGroup=optSet3)
    optItem3a.save()
    optItem3b = OptionItem(name="Soft cover", value="soft", displayOrder=2, price_change=1.00, optionGroup=optSet3)
    optItem3b.save()
    optItem3c = OptionItem(name="On tape", value="tape", displayOrder=3, optionGroup=optSet3)
    optItem3c.save()


    #Add the option group to our items
    i1.option_group.add(optSet1)
    i1.save()
    i1.option_group.add(optSet2)
    i1.save()
    i2.option_group.add(optSet1)
    i2.save()

    i3.option_group.add(optSet3)
    i3.save()
    
    i4.option_group.add(optSet3)
    i4.save()
    print "Creating sub items..."
    #Create the required sub_items
    i1.create_subs = True
    i1.save()
    i2.create_subs = True
    i2.save()
    i3.create_subs = True
    i3.save()
    i4.create_subs = True
    i4.save()
    #This doesn't work yet
    #print "Adding images to the items"
    #image1 = ItemImage(item=i1, sort=1)
    #image1.save()
    #image1.picture = "./images/django-rocks.gif"
    #image1.save()
    #image2 = ItemImage(item=i2, picture="./images/python-rocks.gif", sort=1)
    #image2.save()
    #image3 = ItemImage(item=i3, picture="./images/really-neat-book.gif", sort=1)
    #image3.save()
    #image4 = ItemImage(item=i4, picture="./images/robots-attack.gif", sort=1)
    #image4.save()
    
    print "Create a test user..."
    user = User.objects.create_user('csmith', 'tester@testsite.com', 'test')
    user.save()
    c1.user = user
    c1.save()


def eraseDB(): 
    """Erase database and init it"""
    try: 
        site, settings = find_site()
        delete_db(settings)
        init_and_install()
    except AssertionError, ex: 
        print ex.args[0]

def load_webda():
    """Load internationalization data"""
    baseURL = "http://svn.webda.python-hosting.com/branches"
    dataFile = "Webda-0.9.1.tar.gz"
    print "Retrieving data files..."
    if os.path.isfile(dataFile):
        print "%s - already exists.  Skipping download" % dataFile
    else:
        urllib.urlretrieve(baseURL+"/"+dataFile, dataFile)
    print "Extracting files..."
    #Use tarfile so it's easier on Windows boxes
    #File moves are required for windows but work fine in unix
    #Extract all is in newer python versions.  Drop back to system
    #calls if this doesn't work
    try:
        tar = tarfile.open(dataFile, 'r:gz')
        tar.extractall()
        tar.close()
        if os.path.exists("./i18n/data"):
            shutil.rmtree("./i18n/data")
        shutil.move("./data","./i18n/data")
    except AttributeError:
        os.system('tar -xvzf %s -C ./i18n' % dataFile)

def load_US_tax_table():
    """ Load a simple sales tax table for the US """
    from satchmo.tax.models import TaxRate, TaxClass
    from satchmo.i18n.models import Area, Country
    us = Country.objects.get(iso2_code="US")
    defaultTax = TaxClass(description="Default", title="Default")
    defaultTax.save()
    dataFile = "tax-table.csv"
    dataDir = os.path.join(settings.DIRNAME,"tax/data")
    reader = csv.reader(open(os.path.join(dataDir, dataFile), "rb"))
    reader.next()       #Skip the header row
    for row in reader:
        state = Area.objects.get(country=us, abbrev=row[0])
        stateTax = TaxRate(taxClass=defaultTax, taxZone=state, percentage=row[1])
        stateTax.save()        
    
if __name__ == '__main__': 
    responseWebda = string.lower(raw_input("Type 'yes' to load internationalization data: "))
    if responseWebda == 'yes':
        load_webda()
    response = string.lower(raw_input("Type 'yes' to erase the database and reinstall all models: "))
    if response == 'yes':
        eraseDB()
    if responseWebda =='yes':
        import webda
        webda.main()
    response = string.lower(raw_input("Type 'yes' to load sample store data: "))
    if response == 'yes':
        load_data()
    response = string.lower(raw_input("Type 'yes' to load a tax table for the US: "))
    if response == 'yes':
        load_US_tax_table()

   

