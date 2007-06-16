"""Pluggable newsletter handling."""

from django.conf import settings
import sys

class SubscriptionManager(object):
    """A singleton manager for Newsletter Subscription handling."""

    __instance = None

    def __init__(self):
        if SubscriptionManager.__instance is None:
            
            try:
                modulename = settings.NEWSLETTER_MODULE
            except AttributeError:
                modulename = 'satchmo.newsletter.ignore'
                
            __import__(modulename)            
            SubscriptionManager.__instance = sys.modules[modulename]
        
        self.__dict__['_SubscriptionManager__instance'] = SubscriptionManager.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __getitem__(self, key):
        return self.__instance[key]

    def __len__(self):
        return len(self.__instance)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)

    def __str__(self):
        return "SubscriptionManager: " + str(self.__instance)
