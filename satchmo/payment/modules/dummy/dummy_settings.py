# Settings which configure the "dummy" no-op payment processor
# These settings get loaded by PaymentSettings() using the setting
# PAYMENT_MODULES
#
# for example, to load this one, you would have something like this
# PAYMENT_MODULES = ('satchmo.payment.modules.dummy.dummy_settings',)

gettext = lambda s: s
PAYMENT_LIVE = False

# REQUIRED FIELDS are LABEL, KEY, MODULE, URL_BASE
# where to find the modules which this payment module requires
MODULE = 'satchmo.payment.modules.dummy'

# what this will be called on checkout screens
LABEL = gettext('Dummy processor')

# The key used to look up from PaymentSettings()
KEY = 'DUMMY' 

# The url base used for constructing urlpatterns
# which will call the views defined by this module
URL_BASE = r'^dummy/' 

# if SSL is not specified, it will default to the CHECKOUT_SSL setting in your main settings file
#SSL = False

PAYMENTCHOICES = (
    (gettext('Dummy CreditCard'), gettext('Dummy CreditCard')),
)

# Available Credit Cards on the checkout page for this module.
CREDITCHOICES = (
    (('Visa','Visa')),
    (('Mastercard','Mastercard')),
    (('Discover','Discover')),
)

if PAYMENT_LIVE:
    print("%s Payment is LIVE - Probably you don't want DUMMY live" % KEY)
#else:
#    print("%s Payment DEBUG SANDBOX" % KEY)
