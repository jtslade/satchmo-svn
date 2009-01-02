from livesettings import config_register, StringValue, IntegerValue, BooleanValue
from satchmo_store.shop.config import SHOP_GROUP

from django.utils.translation import ugettext_lazy as _

config_register(
    BooleanValue(SHOP_GROUP,
    'AUTHENTICATION_REQUIRED',
    description=_("Only authenticated users can check out"),
    help_text=_("Users will be required to authenticate (and create an account if neccessary) before checkout."),
    default=False,
    )
)

config_register(
    BooleanValue(SHOP_GROUP,
    'BILLING_DATA_OPTIONAL',
    description=_("Billing data is optional"),
    help_text=_(
        "Users will not be required to provide billing address and phone number. If authentication "
        "before checkout is required, this allows instant purchase (all required contact data will "
        "have already been provided in registration form). Otherwise be careful, as this may leave "
        "you orders with almost no customer data!"
        ),
    default=False,
    )
)
# I am doing it this way instead of a boolean for email verification because I
# intend to add a "manual approval" style of account verification. -Bruce
ACCOUNT_VERIFICATION = config_register(StringValue(SHOP_GROUP,
    'ACCOUNT_VERIFICATION',
    description=_("Account Verification"),
    help_text=_("Select the style of account verification.  'Immediate' means no verification needed."),
    default="IMMEDIATE",
    choices=[('IMMEDIATE', _('Immediate')),
             ('EMAIL', _('Email'))]
    ))
             
config_register(
    IntegerValue(SHOP_GROUP,
    'ACCOUNT_ACTIVATION_DAYS',
    description=_('Days to verify account'),
    default=7,
    requires=ACCOUNT_VERIFICATION,
    requiresvalue='EMAIL')
)
