from django import newforms as forms
from django.newforms import widgets
from django.template import RequestContext, Context
from django.template import loader
from django import http
from django.shortcuts import render_to_response
from django.core.mail import send_mail
from satchmo.shop.models import Config
from django.conf import settings

#Choices displayed to the user to categorize the type of contact request
email_choices = (
    ("General Question", "General question"),
    ("Order Problem", "Order problem"),
)

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    sender = forms.EmailField(label="Email Address")
    subject = forms.CharField()
    inquiry = forms.ChoiceField(choices=email_choices)
    contents = forms.CharField(widget=widgets.Textarea(attrs = {'cols': 40, 'rows': 5}))

def form(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            new_data = form.cleaned_data
            t = loader.get_template('email/contact_us.txt')
            c = Context({
                'request_type': new_data['inquiry'],
                'name': new_data['name'],
                'email': new_data['sender'],    
                'request_text': new_data['contents'] })
            subject = new_data['subject']
            shop_config = Config.objects.get(site=settings.SITE_ID)
            shop_email = shop_config.storeEmail
            send_mail(subject, t.render(c), shop_email,
                     [shop_email], fail_silently=False)
            return http.HttpResponseRedirect('%s/contact/thankyou' % (settings.SHOP_BASE))
    else: #Not a post so create an empty form
        initialData = {}
        if request.user.is_authenticated():
            initialData['sender'] = request.user.email
            initialData['name'] = request.user.first_name + " " + request.user.last_name
        form = ContactForm(initial=initialData)
        

    return render_to_response('contact_form.html', {'form': form},
                                RequestContext(request))

