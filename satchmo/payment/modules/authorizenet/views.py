from satchmo.payment.paymentsettings import PaymentSettings
from satchmo.payment.common.views import credit_confirm, credit_payship
    
def pay_ship_info(request):
    return credit_payship.pay_ship_info(request, PaymentSettings().AUTHORIZENET)
    
def confirm_info(request):
    return credit_confirm.confirm_info(request, PaymentSettings().AUTHORIZENET)