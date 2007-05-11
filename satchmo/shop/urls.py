import os
from django.conf import settings
from django.conf.urls.defaults import *
from satchmo.product.models import Item

#The following views are custom to Satchmo

urlpatterns = []
if hasattr(settings, 'SHOP_URLS'):
    urlpatterns += settings.SHOP_URLS

urlpatterns += patterns('satchmo.shop.views',
     (r'^category/(?P<slug>[-\w]+)/$','category.root'),
     (r'^category/(?P<slug_parent>[-\w]+)/(?P<slug>[-\w]+)/$','category.children'),
     (r'^category/([-\w]+/)+(?P<slug_parent>[-\w]+)/(?P<slug>[-\w]+)/$','category.children'),
     (r'^cart/(?P<id>\d+)/add/$', 'cart.add', {}, 'satchmo_cart_add'),
     (r'^cart/(?P<id>\d+)/remove/$', 'cart.remove', {}, 'satchmo_cart_remove'),
     (r'^cart/$', 'cart.display', {}, 'satchmo_cart'),
     (r'^account/create/$', 'account.create', {}, 'satchmo_account_create'),
     (r'^account/info/$', 'account.info', {}, 'satchmo_account_info'),
     (r'^account/logout/$', 'account.shop_logout', {}, 'satchmo_logout'),
     (r'^contact/$', 'contact.form', {}, 'satchmo_contact'),
     (r'^checkout/$', 'credit_card.checkout_step1.contact_info', {'SSL':False}, 'satchmo_checkout-step1'),
     (r'^checkout/pay/$', 'credit_card.checkout_step2.pay_ship_info', {'SSL':False}, 'satchmo_checkout-step2'),
     (r'^checkout/confirm/$', 'credit_card.checkout_step3.confirm_info', {'SSL':False}, 'satchmo_checkout-step3'),
     (r'^checkout/success/$', 'common.checkout_success', {'SSL':False}, 'satchmo_checkout-success')
)
#Note with the last category url - this allows category depth to be as deep as we want but the downside
#is that we ignore all but the child and parent category.  In practice this should be ok

urlpatterns += patterns('satchmo.product.views',
    (r'^product/(?P<slug>[-\w]+)/prices/$','get_price'),
    (r'^search/$', 'do_search', {}, 'satchmo_search'),
    (r'^product/(?P<slug>[-\w]+)/$','get_item'),
    (r'^product/(?P<slug>[-\w]+)/(?P<subitemId>[\d]+)/$','get_item'),
)


#Dictionaries for generic views used in Satchmo

index_dict = {
    'queryset': Item.objects.filter(active='1').filter(featured='1'),
    'template_object_name': 'all_items',
    'template_name': 'base_index.html',
    'allow_empty': True,
    'paginate_by': 10,
}

urlpatterns += patterns('django.views.generic',
                        (r'^$','list_detail.object_list',index_dict),
                        (r'^contact/thankyou/$','simple.direct_to_template',{'template':'thanks.html'}),
                        (r'^account/thankyou/$','simple.direct_to_template',{'template':'account_thanks.html'}),                           
                        )

#Dictionary for authentication views
password_reset_dict = {
    'template_name': 'password_reset_form.html',
    'email_template_name': 'email/password_reset.txt',
}
                        
urlpatterns += patterns('django.contrib.auth.views',
                        (r'^account/login/$', 'login', {'template_name': 'login.html'}, 'satchmo_login'),
                        (r'^account/password_reset/$','password_reset', password_reset_dict, 'satchmo_password_reset'),
                        (r'^account/password_reset/done/$', 'password_reset_done', {'template_name':'password_reset_done.html'}, 'satchmo_reset_done'),
                        (r'^account/password_change/$', 'password_change', {'template_name':'password_change_form.html'}, 'satchmo_password_change'),
                        (r'^account/password_change/done/$', 'password_change_done', {'template_name':'password_change_done.html'}, 'satchmo_change_done'),
                        )
  

#Make sure thumbnails and images are served up properly when using the dev server
if settings.LOCAL_DEV:
    urlpatterns += patterns('',
        (r'^site_media/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
