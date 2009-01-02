from django.conf import settings
from django.utils.translation import gettext_lazy as _
from livesettings import config_value
from satchmo_store.shop.exceptions import OutOfStockError
import logging

log = logging.getLogger('shop.listeners')

def veto_out_of_stock(sender, cartitem=None, added_quantity=0, **kwargs):
    """Listener which vetoes adding products to the cart which are out of stock."""
    
    if config_value('PRODUCT','NO_STOCK_CHECKOUT') == False:
        product = cartitem.product
        need_qty = cartitem.quantity + added_quantity
        if product.items_in_stock < need_qty:
            log.debug('out of stock on %s', product.slug)
            raise OutOfStockError(product, product.items_in_stock, need_qty)

def only_one_item_in_cart(sender, cart=None, cartitem=None, **kwargs):
    for item in cart.cartitem_set.all():
        if not item == cartitem:
            log.debug('only one item in cart active: removing %s', item)
            item.delete()
