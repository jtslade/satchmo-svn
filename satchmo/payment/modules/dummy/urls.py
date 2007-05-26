import os
from django.conf.urls.defaults import *
from satchmo.payment.paymentsettings import PaymentSettings

SSL = PaymentSettings().DUMMY.SSL

urlpatterns = patterns('satchmo',
     (r'^$', 'payment.modules.dummy.views.pay_ship_info', {'SSL':SSL}, 'DUMMY_satchmo_checkout-step2'),
     (r'^confirm/$', 'payment.modules.dummy.views.confirm_info', {'SSL':SSL}, 'DUMMY_satchmo_checkout-step3'),
     (r'^success/$', 'shop.views.common.checkout_success', {'SSL':SSL}, 'DUMMY_satchmo_checkout-success'),
)