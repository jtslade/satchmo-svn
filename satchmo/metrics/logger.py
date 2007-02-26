from satchmo.product.models import Item
import logging


class LogMiddleware(object):
    """
    This middleware setups a cache to store information on which items are
    viewed.
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        logger1 = logging.getLogger('stats')
        count = 0
        if view_kwargs.has_key('slug') and view_kwargs.has_key('queryset'):
            if isinstance(view_kwargs['queryset'][0], Item):
                logger1.info("Viewing item %s" % view_kwargs['slug'])
        return None