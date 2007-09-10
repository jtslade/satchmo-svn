import os
from django.conf.urls.defaults import *
from satchmo.payment.paymentsettings import PaymentSettings

SSL = PaymentSettings().GOOGLE.SSL

urlpatterns = patterns('satchmo',
     (r'^$', 'payment.modules.google.views.pay_ship_info', {'SSL': SSL}, 'GOOGLE_satchmo_checkout-step2'),
     (r'^confirm/$', 'payment.modules.google.views.confirm_info', {'SSL': SSL}, 'GOOGLE_satchmo_checkout-step3'),
     (r'^success/$', 'payment.common.views.checkout.success', {'SSL': SSL}, 'GOOGLE_satchmo_checkout-success'),
)
