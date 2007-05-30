# Settings which configure the PayPal payment processor
#
# These settings get loaded by PaymentSettings() using the setting
# PAYMENT_MODULES
#
# You should copy the "paypal_settings-customize.py" file to the
# root of your shop, and rename it "paypal_settings.py". Then you
# can load it using something like this:
# PAYMENT_MODULES = ('paypal_settings',)

gettext = lambda s:s
PAYMENT_LIVE = False

# PAYPAL CUSTOM FIELDS
BUSINESS = '' # The email address for your Paypal account
CURRENCY_CODE = 'USD' # If this is empty or invalid, PayPal assumes USD.
RETURN_ADDRESS = '' # This is the URL that PayPal sends the user to after payment.

# if SSL is not specified, it will default to the CHECKOUT_SSL setting in your main settings file
#SSL = False

POST_URL = 'https://www.paypal.com/cgi-bin/webscr'
if not PAYMENT_LIVE:
    POST_URL = 'https://www.sandbox.paypal.com/cgi-bin/webscr'

# REQUIRED FIELDS are LABEL, KEY, MODULE, URL_BASE
# where to find the modules which this payment module requires
MODULE = 'satchmo.payment.modules.paypal'

# what this will be called on checkout screens
LABEL = gettext('PayPal')

# The key used to look up from PaymentSettings()
KEY = 'PAYPAL'

# The url base used for constructing urlpatterns
# which will call the views defined by this module
URL_BASE = r'^paypal/'
