import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _

class NullContact(object):
    """Simple object emulating a Contact, so that we can add users who aren't Satchmo Contacts.

    Note, this is *not* a Django object, and is not saved to the DB, only to the subscription lists.
    """

    def __init__(self, full_name, email, status):
        if not full_name:
            full_name = email.split('@')[0]

        self.full_name = full_name
        self.email = email
        self.newsletter = status

class Subscription(models.Model):
    """A newsletter subscription."""

    subscribed = models.BooleanField(_('Subscribed'), default=True)
    email = models.EmailField(_('Email'))
    create_date = models.DateField(_("Creation Date"))
    update_date = models.DateField(_("Update Date"))

    def __init__(self, *args, **kwargs):
        super(Subscription, self).__init__(*args, **kwargs)
        self._newstate = self.subscribed

    def __unicode__(self):
        if self.subscribed:
            flag="Y"
        else:
            flag="N"
        return u"[%s] %s" % (flag, self.email)

    def __repr__(self):
        return "<Subscription: %s>" % str(self)

    def update_subscription(self, newstate):
        changed = newstate != self.subscribed
        self.subscribed = newstate
        return changed

    def save(self):
        if not self.id:
            self.create_date = datetime.date.today()

        self.update_date = datetime.date.today()

        super(Subscription, self).save()

