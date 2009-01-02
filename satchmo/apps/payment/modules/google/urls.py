from django.conf.urls.defaults import *
from livesettings import config_get_group, config_value

config = config_get_group('PAYMENT_GOOGLE')

urlpatterns = patterns('',
     (r'^$', 'payment.modules.google.views.pay_ship_info', {'SSL': config.SSL.value}, 'GOOGLE_satchmo_checkout-step2'),
     (r'^confirm/$', 'payment.modules.google.views.confirm_info', {'SSL': config.SSL.value}, 'GOOGLE_satchmo_checkout-step3'),
     (r'^success/$', 'payment.views.checkout.success', {'SSL': config.SSL.value}, 'GOOGLE_satchmo_checkout-success'),
)
