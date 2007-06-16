from django.conf import settings
from django.contrib.auth.models import User 
from django.db import models
from django.utils.translation import gettext_lazy as _
import datetime
import sys

class Subscription(models.Model):
    """A newsletter subscription."""
    
    subscribed = models.BooleanField(_('Subscribed'), default=True)
    email = models.EmailField(_('Email'))
    create_date = models.DateField(_("Creation Date"))
    update_date = models.DateField(_("Update Date"))
    
    def __init__(self, *args, **kwargs):        
        super(Subscription, self).__init__(*args, **kwargs)
        self._newstate = self.subscribed
    
    def __str__(self):
        if self.subscribed:
            flag="Y"
        else:
            flag="N"
        return "[%s] %s" % (flag, self.email)
    
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
        