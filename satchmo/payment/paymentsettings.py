"""Manages lookup and loading of named and configured Payment Modules.

In local_settings, these are built like so:
PAYMENT_MODULE_SETTINGS = ['paypal_settings',
                        'authorizenet_settings',
                        'google_settings']

The settings modules are imported by the singleton on first request.
"""
from django.conf import settings
from django.core import urlresolvers
from django.conf.urls.defaults import url
import sys
import types

def _load_module(module):
    __import__(module)
    return sys.modules[module]

class PaymentSettings(object):
    """A singleton manager for PaymentSettings"""

    class __impl(object):
        def __init__(self):
            self.modules = {}
            try:
                self.ordering = [_PaymentModule(module) for module in settings.PAYMENT_MODULES]

                for module in self.ordering:
                    self.modules[module.key] = module
            except AttributeError:
                raise NameError("No PAYMENT_MODULES found in settings")
                
            try:
                self.SSL = settings.CHECKOUT_SSL
            except AttributeError:
                self.SSL = False

        def __getitem__(self, key):
            return self.modules.get(key)

        def __getattr__(self, key):
            return self.modules.get(key)

        def __iter__(self):
            return iter(self.ordering)
            
        def __len__(self):
            return len(self.modules)

        def all(self, key):
            """Combine all values found for the key in all modules"""
            sets = []
            for module in self.ordering:
                try:
                    sets.append(module[key])
                except KeyError:
                    pass

            ret = []
            for set in sets:
                if isinstance(set, (types.ListType, types.TupleType)):
                    for elt in set:
                        if not elt in ret:
                            ret.append(elt)
                else:
                    ret.append(set)

            return ret

        def as_selectpairs(self):
            """Get a list of tuples suitable for use in a select widget for payment modules"""
            return [module.as_selectpair() for module in self]
            
        def keys(self):
            """Return module key list"""
            return [m.key for m in self]
            
        def urlpatterns(self):
            """
            Get the url patterns for all modules.
            This method is intended to be called from some other urls.py module, probably
            the shop.urls
            """            
            return [module.get_urlpattern() for module in self]
            
    __instance = None

    def __init__(self):
        if PaymentSettings.__instance is None:
            PaymentSettings.__instance = PaymentSettings.__impl()
        
        self.__dict__['_PaymentSettings__instance'] = PaymentSettings.__instance

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
        return "PaymentSettings: " + str(self.keys())


class _PaymentModule(object):
    """Wrapper and convenience methods for the values read from the settings module."""
    
    def __init__(self, settingsmodule):
        module = _load_module(settingsmodule)
        self.key = module.KEY
        self.label = module.LABEL
        self._modulename = module.MODULE
        self._module = module
        
    def _SSL(self):
        try:
            return self._module.SSL
        except AttributeError:
            return PaymentSettings().SSL
        
    SSL = property(fget=_SSL)
        
    def __getattr__(self, key):
        return self._module.__dict__[key]
        
    def __getitem__(self, key):
        if key == "key":
            return self.key
        elif key == "label":
            return self.label
        elif key == "modulename":
            return self._modulename
        else:
            return self._module.__dict__[key]
            
    def __setitem__(self, key, val):
        if key == "key":
            raise ValueError('Cannot reset "key"')
        elif key == "label":
            self.label = val
        elif key == "modulename":
            self._modulename = val
        else:
            self._module.__dict__[key] = val

    def as_selectpair(self):
        """Get a tuple for this module suitable for putting in a select widget."""
        return self.key, self.label

    def get(self, key, val=None):
        """Get any arbitrary field from the settings module."""
        try:
            return self._module[key]
        except KeyError:
            return val

    def get_urlpattern(self):
        """Make a django urlpattern "include" for this payment module.
        
        Will return the equivalent of:
        
        pattern('',
            self.URL_BASE, include(this.modul)
        )
        """
        try:
            return url(self.URL_BASE, [self.make_modulename('urls')])
        except AttributeError:
            raise ValueError("No URL_BASE found for module: %s" % self.key)

    def load(self, module=""):
        """Load an arbitrary child module"""
        n = self.make_modulename(module)
        return _load_module(n)
            
    def load_processor(self):
        """Load the payment processor module"""
        try:
            processor = self._module.PROCESSOR
        except AttributeError:
            processor = self.make_modulename('processor')
            
        return _load_module(processor)
            
    def lookup_template(self, template):
        """Return a template name, which may have been overridden in the settings."""
    
        try:
            return self._module.TEMPLATE_OVERRIDES.get(template,template)
        except AttributeError:
            return template

    def lookup_url(self, name):
        """Look up a named URL for the payment module.
        
        Tries a three-level specific-to-general lookup chain, returning
        the first positive hit.
        
         If there is a dictionary named 
        URL_OVERRIDES, then use the resulting name
        else try prepending the module name to the name
        else just look up the name"""
        url = None
        try:
            override = self._module.URL_OVERRIDES[name]
            try:
                url = urlresolvers.reverse(override)
            except urlresolvers.NoReverseMatch:
                pass
        
        except KeyError:
            pass
        
        except AttributeError:
            try:
                url = urlresolvers.reverse(self.key + "_" + name)
            except urlresolvers.NoReverseMatch:
                pass
            
        if not url:
            url = urlresolvers.reverse(name)
            
        return url
    
    def make_modulename(self, module):
        n = self['modulename']
        if module:
            n = n + "." + module
        return n
        
    def __str__(self):
        return "Payment Module Settings: " + self.key


