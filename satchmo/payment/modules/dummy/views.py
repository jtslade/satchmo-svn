"""Simple wrapper for standard checkout as implemented in satchmo.payment.common.views"""

from satchmo.payment.paymentsettings import PaymentSettings
from satchmo.payment.common.views import confirm, payship
    
def pay_ship_info(request):
    return payship.credit_pay_ship_info(request, PaymentSettings().DUMMY)
    
def confirm_info(request):
    return confirm.credit_confirm_info(request, PaymentSettings().DUMMY)


