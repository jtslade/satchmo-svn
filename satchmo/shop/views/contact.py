from django import oldforms as forms
from django.template import RequestContext, Context
from django.template import loader
from django import http
from django.shortcuts import render_to_response
from django.core.mail import send_mail

#Choices displayed to the user to categorize the type of contact request
email_choices = (
    ("General Question", "General question"),
    ("Order Problem", "Order problem"),
)

class ContactFormManipulator(forms.Manipulator):
    def __init__(self):
        self.fields = (
            forms.TextField(field_name="name", length=20, is_required=True),
            forms.EmailField(field_name="email", length=30, is_required=True),
            forms.TextField(field_name="subject", length=30, maxlength=200, is_required=True),
            forms.SelectField(field_name="inquiry", choices=email_choices),
            forms.LargeTextField(field_name="contents", is_required=True),
        )


def form(request):
    manipulator = ContactFormManipulator()
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            manipulator.do_html2python(new_data)
            t = loader.get_template('email/contact_us.txt')
            c = Context({
            'request_type': new_data['inquiry'],
            'name': new_data['name'],
            'email': new_data['email'],    
            'request_text': new_data['contents'] })
            subject = new_data['subject']
            shop_config = Config.objects.get(site=settings.SITE_ID)
            shop_email = shop_config.storeEmail
            send_mail(subject, t.render(c), shop_email,
                     [shop_email], fail_silently=False)
            return http.HttpResponseRedirect('%s/contact/thankyou' % (settings.SHOP_BASE))
    else:
        errors = new_data = {}
        if request.user.is_authenticated():
            new_data['email'] = request.user.email
            new_data['name'] = request.user.first_name + " " + request.user.last_name
            errors = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('contact_form.html', {'form': form},
                                RequestContext(request))

