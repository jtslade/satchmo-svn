# This file is used to store your site specific settings
# for database access.
# It also store satchmo unique information
#
#
# Modify this file to reflect your settings, then rename it to 
# local_settings.py
#
# This file is helpful if you have an existing Django project.  
# These are specific things that Satchmo will need.
# you MUST make sure these settings are imported from your project settings file!

import os
import logging
DIRNAME = os.path.dirname(__file__)

# This is useful, since satchmo is not the "current directory" like load_data expects.
# SATCHMO_DIRNAME = ''

# Only set these if Satchmo is part of another Django project
#SITE_NAME = ''
#ROOT_URLCONF = ''
#MEDIA_ROOT = os.path.join(DIRNAME, 'static/')
#DJANGO_PROJECT = 'Your Main Project Name'
#DJANGO_SETTINGS_MODULE = 'main-project.settings'

# Make sure Satchmo templates are added to your existing templates
# TEMPLATE_DIRS += (
#    os.path.join(SATCHMO_DIRNAME, "templates"),
#)

# Make sure Satchmo context processor is called
# TEMPLATE_CONTEXT_PROCESSORS += ('satchmo.shop.context_processors.settings')

DATABASE_NAME = ''
DATABASE_PASSWORD = ''
DATABASE_USER = ''
SECRET_KEY = ''

##### For Email ########
# If this isn't set in your settings file, you can set these here
#EMAIL_HOST = 'host here'
#EMAIL_PORT = 587
#EMAIL_HOST_USER = 'your user here'
#EMAIL_HOST_PASSWORD = 'your password'
#EMAIL_USE_TLS = True

#### Satchmo unique variables ####
#This is the base url for the shop.  Only include a leading slash
#examples: '/shop' or '/mystore'
#If you want the shop at the root directory, set SHOP_BASE = ''
SHOP_BASE = '/shop'

#These are used when loading the test data
SITE_DOMAIN = "example.com"
SITE_NAME = "My Site"

# These can override or add to the default URLs
from django.conf.urls.defaults import *
URLS = patterns('',
)
SHOP_URLS = patterns('satchmo.shop.views',
#    (r'^checkout/pay/$', 'paypal.checkout_step2.pay_ship_info', {'SSL': False}, 'satchmo_checkout-step2'),
#    (r'^checkout/confirm/$', 'paypal.checkout_step3.confirm_info', {'SSL': False}, 'satchmo_checkout-step3'),
)

# register custom external newsletter modules by listing their modules here
# ex: CUSTOM_NEWSLETTER_MODULES = ['client.newsletter.autoresponder',]
CUSTOM_NEWSLETTER_MODULES = []

# register custom external payment modules by listing their modules here
# ex: CUSTOM_NEWSLETTER_MODULES = ['client.payment.wondercharge',]
CUSTOM_PAYMENT_MODULES = []

# register custom external shipping modules by listing their modules here
# ex: CUSTOM_NEWSLETTER_MODULES = ['client.shipping.fancyshipping',]
CUSTOM_SHIPPING_MODULES = []

# register custom external product modules by listing their modules here
# ex: CUSTOM_NEWSLETTER_MODULES = ['client.product.myproducttype',]
CUSTOM_PRODUCT_MODULES = []

# a cache backend is required.  Do not use locmem, it will not work properly at all in production
# Preferably use memcached, but file or DB is OK.  File is faster, I don't know why you'd want to use
# db, personally.  See: http://www.djangoproject.com/documentation/cache/ for help setting up your
# cache backend
#CACHE_BACKEND = "memcached://127.0.0.1:11211/"
CACHE_BACKEND = "file:///var/tmp/django_cache"
CACHE_TIMEOUT = 60*5

# Locale path settings.  Needs to be set for Translation compilation.
# It can be blank
# LOCALE_PATHS = ""

#Configure logging
LOGDIR = DIRNAME
LOGFILE = "satchmo.log"
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=os.path.join(LOGDIR, LOGFILE),
                    filemode='w')

# define a Handler which writes INFO messages or higher to the sys.stderr
fileLog = logging.FileHandler(os.path.join(LOGDIR, LOGFILE), 'w')
fileLog.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
fileLog.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(fileLog)
logging.getLogger('caching').setLevel(logging.INFO)
logging.info("Satchmo Started")
