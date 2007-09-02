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

# The default state for SSL in payment sections
CHECKOUT_SSL=False

# Your payment modules are configured in standalone settings files.
#
# No more putting AUTHORIZENET_URL=xxx or any such settings in this file
# Just keep those settings in the appropriate with the payment settings standalone
# file.
#
# To activate any of the modules, please copy the xxx_settings-customize.py
# file from its module at satchmo.payment.modules.xxx, customize and save
# wherever you like.  I suggest the root of the store, alongside the local_settings.py
# file.  Dummy is safe to load from the module itself, since what would be the point
# of customizing that one?

PAYMENT_MODULES = (
    'satchmo.payment.modules.dummy.dummy_settings',
#    'satchmo.paypal_settings',
#    'satchmo.authorizenet_settings',
#    'satchmo.google_settings'
)

# Google Analytics
# Set this to True if you wish to enable Google Analytics.  You must have
# a google ID in order for this to work
GOOGLE_ANALYTICS = False
# If google is enabled, enter the full google code here - Example "UA-abcd-1"
GOOGLE_ANALYTICS_CODE = "UA-xxxx-x"

# Google Adwords
GOOGLE_ADWORDS = False
GOOGLE_ADWORDS_ID = 'your adwords id'

##### For Email ########
# If this isn't set in your settings file, you can set these here
#EMAIL_HOST = 'host here'
#EMAIL_PORT = 587
#EMAIL_HOST_USER = 'your user here'
#EMAIL_HOST_PASSWORD = 'your password'
#EMAIL_USE_TLS = True

# Used by registration application.
# Read docs/email-verification.txt before enabling.
REQUIRE_EMAIL_VERIFICATION = False
ACCOUNT_ACTIVATION_DAYS = 7 # Days until activation code expires.

#### Satchmo unique variables ####
#This is the base url for the shop.  Only include a leading slash
#examples: '/shop' or '/mystore'
#If you want the shop at the root directory, set SHOP_BASE = ''
SHOP_BASE = '/shop'

# Currency symbol to use
CURRENCY = u'$'

#Directory name for storing uploaded images.  This value will be appended
#to MEDIA_ROOT
#If left blank, it will default to images.  Do not prepend name with a slash
#IMAGE_DIR = "pictures"

#These are used when loading the test data
SITE_DOMAIN = "example.com"
SITE_NAME = "My Site"

#Shipping Modules to enable
SHIPPING_MODULES = ['satchmo.shipping.modules.per', 'satchmo.shipping.modules.flat']

# These can override or add to the default URLs
from django.conf.urls.defaults import *
URLS = patterns('',
)
SHOP_URLS = patterns('satchmo.shop.views',
#    (r'^checkout/pay/$', 'paypal.checkout_step2.pay_ship_info', {'SSL': False}, 'satchmo_checkout-step2'),
#    (r'^checkout/confirm/$', 'paypal.checkout_step3.confirm_info', {'SSL': False}, 'satchmo_checkout-step3'),
)

PRODUCT_TYPES = (
    ('product', 'ConfigurableProduct'),
    ('product', 'ProductVariation'),
#    ('product', 'DownloadableProduct'),
#    ('product', 'BundledProduct'),
)

#### Newsletter Settings
# This is optional.  Make sure to add satchmo.newsletter to your INSTALLED_APPS if you want to use it.
#NEWSLETTER_MODULE = 'satchmo.newsletter.mailman'
# required for mailman module
#NEWSLETTER_NAME = 'ooh-ga-boo-ga'

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
logging.info("Satchmo Started")
