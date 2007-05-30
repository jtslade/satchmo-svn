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

# AUTHORIZE_NET CUSTOM FIELDS
CONNECTION = 'https://test.authorize.net/gateway/transact.dll'
TEST = 'TRUE'
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
