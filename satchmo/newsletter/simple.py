""" Just tracks subscriptions, nothing more. """

from satchmo.newsletter.models import Subscription
from django.utils.translation import ugettext as _

def update_contact(contact):
    sub, created = Subscription.objects.get_or_create(email=contact.email)
    if contact.newsletter != None:
        changed = sub.update_subscription(contact.newsletter)

        result = ""

        if created or changed:
            sub.save()
            if sub.subscribed:
                result = _("Subscribed: %(email)s") % {'email': contact.email}
            else:
                result = _("Unsubscribed: %(email)s") % {'email': contact.email}

        else:
            if sub.subscribed:
                result = _("Already subscribed.")
            else:
                result = _("Already removed.")

        return result

