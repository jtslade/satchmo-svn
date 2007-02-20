from django.conf.urls.defaults import *
import os
from django.conf import settings
from satchmo.product.models import Item

#The following views are custom to Satchmo

urlpatterns = patterns('satchmo.shop.views',
     (r'^category/(?P<slug>[-\w]+)/$','category.root'),
     (r'^category/(?P<slug_parent>[-\w]+)/(?P<slug>[-\w]+)/$','category.children'),
     (r'^category/([-\w]+/)+(?P<slug_parent>[-\w]+)/(?P<slug>[-\w]+)/$','category.children'),
     (r'^cart/(?P<id>\d+)/add/$','cart.add'),
     (r'^cart/(?P<id>\d+)/remove/$','cart.remove'),
     (r'^cart/$','cart.display'),
     (r'^account/create/$','account.create'),
     (r'^account/info/$','account.info'),
     (r'^account/logout/$','account.shop_logout'),
     (r'^contact/$','contact.form'),
     (r'^checkout/$','checkout-step1.contact_info'),
     (r'^checkout/pay/$','checkout-step2.pay_ship_info'),  
     (r'^checkout/confirm/$','checkout-step3.confirm_info'),     
)
#Note with the last category url - this allows category depth to be as deep as we want but the downside
#is that we ignore all but the child and parent category.  In practice this should be ok

urlpatterns += patterns('satchmo.product.views',
    (r'^product/(?P<slug>[-\w]+)/prices/$','get_json'),
)


#Dictionaries for generic views used in Satchmo

index_dict = {
    'queryset': Item.objects.filter(active="1").filter(featured="1"),
    'template_object_name': 'all_items', 
    'template_name' : 'base_index.html',
    'allow_empty': True,      
    'paginate_by' : 10,        
}

product_dict = {
    'queryset': Item.objects.filter(active="1"),
    'slug_field' : 'short_name',
    'template_object_name' : 'item', 
    'template_name': 'base_product.html',
}


urlpatterns += patterns('django.views.generic',
                        (r'^$','list_detail.object_list',index_dict),
                        (r'^product/(?P<slug>[-\w]+)/$','list_detail.object_detail',product_dict),
                        (r'^contact/thankyou/$','simple.direct_to_template',{'template':'thanks.html'}),
                        (r'^account/thankyou/$','simple.direct_to_template',{'template':'account_thanks.html'}),
                        (r'^checkout/success/$','simple.direct_to_template',{'template':'checkout_success.html'}),                            
                        )

#Dictionary for authentication views
password_reset_dict = {
    'template_name': 'password_reset_form.html',
    'email_template_name': 'email/password_reset.txt',
}
                        
urlpatterns += patterns('django.contrib.auth.views',
                        (r'^account/login/$', 'login', {'template_name': 'login.html'}),
                        (r'^account/password_reset/$','password_reset', password_reset_dict),
                        (r'^account/password_reset/done/$', 'password_reset_done', {'template_name':'password_reset_done.html'}),
                        (r'^account/password_change/$', 'password_change', {'template_name':'password_change_form.html'}),
                        (r'^account/password_change/done/$', 'password_change_done', {'template_name':'password_change_done.html'}),
                        )
  

#Make sure thumbnails and images are served up properly when using the dev server
if settings.LOCAL_DEV:
    urlpatterns += patterns('',
        (r'^site_media/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )