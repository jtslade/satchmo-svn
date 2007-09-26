"""A Mailman newsletter subscription interface.

To use this plugin, enable the newsletter module and set the newsletter module and name settings
in the admin settings page.
"""

from django.utils.translation import ugettext as _
from Mailman import MailList, Errors
from satchmo.newsletter.models import Subscription
from satchmo.configuration import config_value
import sys

class UserDesc: pass

def update_contact(contact):
    """Automatically called by Contact.save(), which keeps it in sync with the Contact newsletter setting."""
    sub = None
    changed = False

    sub, created = Subscription.objects.get_or_create(email=contact.email)
    changed = sub.update_subscription(contact.newsletter)

    result = ""

    if created or changed:
        sub.save()
    else:
        if sub.subscribed:
            result = _("Already subscribed.")
        else:
            result = _("Already removed.")

    if sub.subscribed:
        mailman_add(contact)
        result = _("Subscribed: %(email)s") % { 'email' : contact.email }
    else:
        mailman_remove(contact)
        result = _("Unsubscribed: %(email)s") % { 'email' : contact.email }

    return result

def mailman_add(contact, listname=None, send_welcome_msg=None, admin_notify=None):
    """Add a Satchmo contact to a mailman mailing list.

    Parameters:
        - `Contact`: A Satchmo Contact
        - `listname`: the Mailman listname, defaulting to whatever you have set in settings.NEWSLETTER_NAME
        - `send_welcome_msg`: True or False, defaulting to the list default
        - `admin_notify`: True of False, defaulting to the list default
    """
    mm, listname = _get_maillist(listname)
    print >> sys.stderr, 'mailman adding %s to %s' % (contact.email, listname)

    if send_welcome_msg is None:
        send_welcome_msg = mm.send_welcome_msg

    userdesc = UserDesc()
    userdesc.fullname = contact.full_name
    userdesc.address = contact.email
    userdesc.digest = False

    if mm.isMember(contact.email):
        print >> sys.stderr, _('Already Subscribed: %s' % contact.email)

    else:
        try:
            try:
                mm.Lock()
                mm.ApprovedAddMember(userdesc, send_welcome_msg, admin_notify)
                mm.Save()
                print >> sys.stderr, _('Subscribed: %(email)s') % { 'email' : contact.email }

            except Errors.MMAlreadyAMember:
                print >> sys.stderr, _('Already a member: %(email)s') % { 'email' : contact.email }

            except Errors.MMBadEmailError:
                if userdesc.address == '':
                    print >> sys.stderr, _('Bad/Invalid email address: blank line')
                else:
                    print >> sys.stderr, _('Bad/Invalid email address: %(email)s') % { 'email' : contact.email }

            except Errors.MMHostileAddress:
                print >> sys.stderr, _('Hostile address (illegal characters): %(email)s') % { 'email' : contact.email }

        finally:
            mm.Unlock()

def mailman_remove(contact, listname=None, userack=None, admin_notify=None):
    """Remove a Satchmo contact from a Mailman mailing list

    Parameters:
        - `contact`: A Satchmo contact
        - `listname`: the Mailman listname, defaulting to whatever you have set in settings.NEWSLETTER_NAME
        - `userack`: True or False, whether to notify the user, defaulting to the list default
        - `admin_notify`: True or False, defaulting to the list default
    """


    mm, listname = _get_maillist(listname)
    print >> sys.stderr, 'mailman removing %s from %s' % (contact.email, listname)

    if mm.isMember(contact.email):
        try:
            mm.Lock()
            mm.ApprovedDeleteMember(contact.email, 'satchmo.newsletter',  admin_notify, userack)
            mm.Save()
        finally:
            mm.Unlock()

def _get_maillist(listname):
    try:
        if not listname:
            listname = config_value('NEWSLETTER', 'NEWSLETTER_NAME')

        if listname == "":
            log.warn("NEWSLETTER_NAME not set in store settings")
            raise NameError('No NEWSLETTER_NAME in settings')

        return MailList.MailList(listname, lock=0), listname

    except Errors.MMUnknownListError:
        print >> sys.stderr, "Can't find the MailMan newsletter: %s" % listname
        raise NameError('No such newsletter, "%s"' % listname)
