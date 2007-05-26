import os
from django.conf.urls.defaults import *
from satchmo.payment.paymentsettings import PaymentSettings

paymentsettings = PaymentSettings()

# this is set in your settings file under "SSL", and becomes the default SSL setting for all
# payment modules
SSL = paymentsettings.SSL

urlpatterns = patterns('satchmo.payment.views',
     (r'^$', 'contact_info', {'SSL':SSL}, 'satchmo_checkout-step1'),
)

# now add all enabled module payment settings
urlpatterns += paymentsettings.urlpatterns()  
