"""Pluggable newsletter handling."""

from satchmo.configuration import config_value
from satchmo.shop.utils import load_module

class SubscriptionManager(object):
    """A singleton manager for Newsletter Subscription handling."""

    __instance = None

    def __init__(self):
        if SubscriptionManager.__instance is None:
            
            try:
                modulename = config_value('NEWSLETTER', 'MODULE')
            except AttributeError:
                modulename = 'satchmo.newsletter.ignore'
                
            module = load_module(modulename)
            SubscriptionManager.__instance = module
        
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
