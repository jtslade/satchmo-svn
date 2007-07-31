# Settings which configure the "authorize.net" payment processor
# You *must* have an Authorize.net account for this to work.
#
# These settings get loaded by PaymentSettings() using the setting
# PAYMENT_MODULES
#
# You should copy the authorizenet_settings-customize.py file to the
# root of your shop, and rename it authorizenet_settings.  Then you
# can load it using something like this:
# PAYMENT_MODULES = ('authorizenet_settings',)

gettext = lambda s:s
PAYMENT_LIVE = False

# A Quick note on the urls
# If you are posting to https://test.authorize.net/gateway/transact.dll,
# and you are not using an account whose API login ID starts with
# "cpdev" or "cnpdev", you will get an Error 13 message. 
# Make sure you are posting to https://secure.authorize.net/gateway/transact.dll for
# live transactions, or https://certification.authorize.net/gateway/transact.dll
# for test transactions if you do not have a cpdev or cnpdev.

# AUTHORIZE_NET CUSTOM FIELDS
CONNECTION = 'https://test.authorize.net/gateway/transact.dll'
TEST = 'TRUE'
# These keys are generated via the Authorize.net website
LOGIN = ''
TRANKEY = ''

# if SSL is not specified, it will default to the CHECKOUT_SSL setting in your main settings file
#SSL = False

if not PAYMENT_LIVE:
    CONNECTION = 'https://test.authorize.net/gateway/transact.dll'
    TEST = 'TRUE'

CREDITCHOICES = (
    (('Visa','Visa')),
    (('Mastercard','Mastercard')),
    (('Discover','Discover')),
)

# REQUIRED FIELDS are LABEL, KEY, MODULE, URL_BASE
# where to find the modules which this payment module requires
MODULE = 'satchmo.payment.modules.authorizenet'

# what this will be called on checkout screens
LABEL = gettext('Credit Cards')

# The key used to look up from PaymentSettings()
KEY = 'AUTHORIZENET' 

# The url base used for constructing urlpatterns
# which will call the views defined by this module
URL_BASE = r'^credit/' 

#if PAYMENT_LIVE:
#    print("%s Payment is LIVE" % KEY)
#else:
#    print("%s Payment DEBUG SANDBOX" % KEY)
