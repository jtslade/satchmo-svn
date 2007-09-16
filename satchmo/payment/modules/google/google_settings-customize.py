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

# ===============================================
# OPTIONS - adjust to your needs

PAYMENT_LIVE = False

# what this will be called on checkout screens.  Leave the gettext, it is
# for the translation utilities and doesn't hurt anything, even if you
# aren't doing a multilingual site.
LABEL = gettext('Google Checkout')

# if SSL is not specified, it will default to the CHECKOUT_SSL setting in your main settings file
#SSL = False

# This is the XML template used to submit the cart to Google
CART_XML_TEMPLATE = "checkout/google/cart.xml"

CURRENCY_CODE = 'USD'

# These are the image sizes offered by Google for the checkout button
# You'll use these with the satchmo_googlecheckout tag
# {% google_checkout_button 'MEDIUM' %}
# please leave the keys upper case!
CHECKOUT_BUTTON_URL = "http://checkout.google.com/buttons/checkout.gif"
CHECKOUT_BUTTON_SIZES = {
    "SMALL" : (160,43),
    "MEDIUM" : (168,44),
    "LARGE" : (180,46)
}

POST_URL = "https://checkout.google.com/cws/v2/Merchant/%(MERCHANT_ID)s/checkout"
MERCHANT_ID = "YOUR-ID-HERE"
MERCHANT_KEY = "YOUR-KEY-HERE"

if not PAYMENT_LIVE:
    POST_URL = "https://sandbox.google.com/cws/v2/Merchant/%(MERCHANT_ID)s/checkout"
    MERCHANT_ID = "YOUR-TESTING-ID-HERE"
    MERCHANT_KEY = "YOUR-TESTING-KEY-HERE"

# ==============================================
# MODULE FIELDS
# Don't edit unless you know what you are doing

# where to find the modules which this payment module requires
MODULE = 'satchmo.payment.modules.google'

# The key used to look up from PaymentSettings()
KEY = 'GOOGLE'

# The url base used for constructing urlpatterns
# which will call the views defined by this module
URL_BASE = r'^google/'
