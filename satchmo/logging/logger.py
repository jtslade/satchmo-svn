from django.core.cache import cache
from satchmo.product.models import Item
from django.settings import *

#Create a cache in memory for 10 minutes
CACHE_BACKEND = 'locmem:///?timeout=60*10'

class LogMiddleware(object):
    """
    This middleware setups a cache to store information on which items are
    viewed.
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        #settings.METRICS.debug('Some stuff')
        count = 0
        if view_kwargs.has_key('slug') and view_kwargs.has_key('queryset'):
            if isinstance(view_kwargs['queryset'][0], Item):
                if cache.get(view_kwargs['slug']):
                    count = cache.get(view_kwargs['slug'])
                cache.set(view_kwargs['slug'], count+1)
            print cache.get(view_kwargs['slug'])
        return None
