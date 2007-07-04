""" Just tracks subscriptions, nothing more. """

from satchmo.newsletter.models import Subscription

def update_contact(contact):
    sub, created = Subscription.objects.get_or_create(email=contact.email)
    if contact.newsletter != None:
        changed = sub.update_subscription(contact.newsletter)
        if created or changed:
            sub.save()
