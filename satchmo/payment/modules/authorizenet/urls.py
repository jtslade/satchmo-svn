import os
from django.conf.urls.defaults import *
from satchmo.payment.paymentsettings import PaymentSettings

SSL = PaymentSettings().AUTHORIZENET.SSL

urlpatterns = patterns('satchmo',
     (r'^$', 'payment.modules.authorizenet.views.pay_ship_info', {'SSL':SSL}, 'AUTHORIZENET_satchmo_checkout-step2'),
     (r'^confirm/$', 'payment.modules.authorizenet.views.confirm_info', {'SSL':SSL}, 'AUTHORIZENET_satchmo_checkout-step3'),
     (r'^success/$', 'payment.common.views.checkout.success', {'SSL':SSL}, 'AUTHORIZENET_satchmo_checkout-success'),
)