import os
from django.conf.urls.defaults import *
from satchmo.payment.paymentsettings import PaymentSettings

SSL = PaymentSettings().PAYPAL.SSL

urlpatterns = patterns('satchmo',
     (r'^$', 'payment.modules.paypal.views.pay_ship_info', {'SSL': SSL}, 'PAYPAL_satchmo_checkout-step2'),
     (r'^confirm/$', 'payment.modules.paypal.views.confirm_info', {'SSL': SSL}, 'PAYPAL_satchmo_checkout-step3'),
     (r'^success/$', 'shop.views.common.checkout_success', {'SSL': SSL}, 'PAYPAL_satchmo_checkout-success'),
)
