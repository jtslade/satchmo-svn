from satchmo import caching
import logging

log = logging.getLogger('caching')

class CachedObjectMixin(object):
    """Provides basic object caching for any objects using this as a mixin."""

    def cache_delete(self, *args, **kwargs):
        key = self.cache_key(*args, **kwargs)
        log.debug("clearing cache for %s", key)
        caching.cache_delete(key, children=True)

    def cache_get(self, *args, **kwargs):
        key = self.cache_key(*args, **kwargs)
        return caching.cache_get(key)

    def cache_key(self, *args, **kwargs):
        keys = [self.__class__.__name__, self]
        keys.extend(args)
        return caching.cache_key(keys, **kwargs)

    def cache_reset(self):
        self.cache_delete()
        self.cache_set()

    def cache_set(self, *args, **kwargs):
        val = kwargs.pop('value', self)
        key = self.cache_key(*args, **kwargs)
        caching.cache_set(key, value=val)
        
    def is_cached(self, *args, **kwargs):
        return caching.is_cached(self.cache_key(*args, **kwargs))
