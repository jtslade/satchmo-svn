# Django settings for satchmo project.
# If you have an existing project, then ensure that you modify local_settings-customize.py
# and import it from your main settings file. (from local_settings import *)
import os

DIRNAME = os.path.abspath(os.path.dirname(__file__).decode('utf-8'))

DJANGO_PROJECT = 'satchmo'
DJANGO_SETTINGS_MODULE = 'satchmo.settings'

LOCAL_DEV = True
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
     ('', ''),
)

MANAGERS = ADMINS

DATABASE_ENGINE = ''           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
# The following variables should be configured in your local_settings.py file
#DATABASE_NAME = ''             # Or path to database file if using sqlite3.
#DATABASE_USER = ''             # Not used with sqlite3.
#DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
# For windows, you must use 'us' instead
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
# Image files will be stored off of this path.
MEDIA_ROOT = os.path.join(DIRNAME, 'static/')
# URL that handles the media served from MEDIA_ROOT. Use a trailing slash.
# Example: "http://media.lawrence.com/"
MEDIA_URL = '/static/'
# URL that handles the media served from SSL.  You only need to set this
# if you are using a non-relative url.
# Example: "https://media.lawrence.com"
# MEDIA_SECURE_URL = "https://foo.com/"
# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
# SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.doc.XViewMiddleware",
    "threaded_multihost.middleware.ThreadLocalMiddleware",
    "satchmo.shop.SSLMiddleware.SSLRedirect",
    "satchmo.recentlist.middleware.RecentProductMiddleware",
)

#this is used to add additional config variables to each request
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.media',
    'satchmo.recentlist.context_processors.recent_products',
    'satchmo.shop.context_processors.settings',
    'django.core.context_processors.i18n'
)

ROOT_URLCONF = 'satchmo.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    os.path.join(DIRNAME, "templates"),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.comments',
    'django.contrib.sessions',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    #'registration',
    'satchmo',
    'satchmo.caching',
    'satchmo.configuration',
    'satchmo.shop',
    'satchmo.contact',
    'satchmo.product',
    # ****
    # * Optional feature, product brands
    # * Uncomment below, and add the brand url in your satchmo_urls setting
    # * usually in local_settings.py
    # ****
    #'satchmo.product.brand',
    'satchmo.shipping',
    'satchmo.payment',
    'satchmo.discount',
    'satchmo.giftcertificate',
    'satchmo.supplier',
    'satchmo.thumbnail',
    'satchmo.l10n',
    'satchmo.tax',
    'satchmo.recentlist',
    'satchmo.wishlist',
    'satchmo.upsell',
    'satchmo.productratings',
    # ****
    # * Optional Feature, Tiered shipping
    # * uncomment below to make that shipping module available in your live site
    # * settings page. enable it there, then configure it in the
    # * admin/tiered section of the main admin page.
    # ****
    #'satchmo.shipping.modules.tiered',
    # ****
    # * Optional feature newsletter
    # ****
    #'satchmo.newsletter',
    # ****
    # * Optional feature product feeds
    # * These are usually for googlebase
    # ****
    #'satchmo.feeds',
    # ****
    # * Optional feature, tiered pricing
    # * uncomment below, then set up in your main admin page.
    # ****
    #'satchmo.product.tieredpricing',
    # ****
    # * Highly recommended app - use this to have access to the great
    # * "Jobs" system.  See http://code.google.com/p/django-command-extensions/
    # * Make sure to set up your crontab to run the daily, hourly and monthly
    # * jobs.
    # ****
    #'django_extensions',
    
)

AUTHENTICATION_BACKENDS = (
    'satchmo.accounts.email-auth.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PROFILE_MODULE='contact.Contact'
LOGIN_REDIRECT_URL = '/accounts/'

SATCHMO_SETTINGS = {
    # this will override any urls set in the store url modules
    #'SHOP_URLS' : patterns('satchmo.shop.views',
    #    (r'^checkout/pay/$', 'paypal.checkout_step2.pay_ship_info', {'SSL': False}, 'satchmo_checkout-step2'),
    #    (r'^checkout/confirm/$', 'paypal.checkout_step3.confirm_info', {'SSL': False}, 'satchmo_checkout-step3'),
    #   if you have satchmo.feeds, make sure to include its URL
    #    (r'^feed/', include('satchmo.feeds.urls')),
    #   likewise with newsletters
    #    (r'^newsletter/', include('satchmo.newsletter.urls'))
    #   enable brands here
    #    (r'^brand/', include('satchmo.product.brand.urls'))
    #}
    
    # This is the base url for the shop.  Only include a leading slash
    # examples: '/shop' or '/mystore'
    # If you want the shop at the root directory, set SHOP_BASE to ''
    'SHOP_BASE' : '/store',
    
    # Set this to true if you want to use the multi-shop features
    # of satchmo.  It requires the "threaded_multihost" application
    # to be on your pythonpath.
    'MULTISHOP' : False,
    
    # This will turn on/off product translations in the admin for products
    'ALLOW_PRODUCT_TRANSLATIONS' : True,
    
    # register custom external newsletter modules by listing their modules here
    # 'CUSTOM_NEWSLETTER_MODULES' : ['client.newsletter.autoresponder',]
    'CUSTOM_NEWSLETTER_MODULES' : [],

    # register custom external payment modules by listing their modules here
    # ex: 'CUSTOM_PAYMENT_MODULES' : ['client.payment.wondercharge',]
    'CUSTOM_PAYMENT_MODULES' : [],

    # register custom external shipping modules by listing their modules here
    # ex: 'CUSTOM_SHIPPING_MODULES' : ['client.shipping.fancyshipping',]
    'CUSTOM_SHIPPING_MODULES' : [],

    # register custom external product modules by listing their modules here
    # ex: 'CUSTOM_PRODUCT_MODULES' : ['client.product.myproducttype',]
    'CUSTOM_PRODUCT_MODULES' : [],
}

# Load the local settings
from local_settings import *

# if you want to use a multi-shop, uncomment the patch
#from threaded_multihost import multihost_patch
