from django.shortcuts import render_to_response
from django.contrib.auth.decorators import user_passes_test
from django import http
from django import oldforms as forms
from django.template import RequestContext, Context
from django.template import loader
from django.core import validators
from django.contrib.auth.forms import AuthenticationForm
from satchmo.shop.models import Config
from django.conf import settings
from satchmo.shop.views.utils import bad_or_missing
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from satchmo.contact.models import Contact
from django.core.mail import send_mail
from satchmo.shop.utils.unique_id import generate_id

class AccountManipulator(AuthenticationForm):
    def __init__(self, request):
        AuthenticationForm.__init__(self, request)
        self.fields = (
            forms.EmailField(field_name="email", length=30, is_required=True, validator_list=[self.isUniqueEmail]),
            forms.PasswordField(field_name="password", length=30, is_required=True),
            forms.PasswordField(field_name="password2", length=30, is_required=True,
                                validator_list=[validators.AlwaysMatchesOtherField('password', "The two password fields didn't match.")]),
            forms.TextField(field_name="first_name",length=30, is_required=True),
            forms.TextField(field_name="last_name",length=30, is_required=True),
            #forms.TextField(field_name="user_name",length=30, is_required=True, validator_list=[self.isUniqueUsername]),
        )
        
    def isValidPassword(self, field_data, all_data):
        if not (field_data == all_data['password']):
            raise validators.ValidationError("Your passwords do not match.")
    
    def isUniqueEmail(self, field_data, all_data):
        if User.objects.filter(email=field_data).count() > 0:
            raise validators.ValidationError("That email address is already in use.")
    
    def isUniqueUsername(self, field_data, all_data):
        try:
            User.objects.get(username=field_data)
        except User.DoesNotExist:
            pass
        else:
            raise validators.ValidationError("That username already exists.")
            
    def save(self, data):
        user_name = generate_id(data['first_name'], data['last_name'])
        password = data['password']
        email = data['email']
        first_name = data['first_name']
        last_name = data['last_name']
        u = User.objects.create_user(user_name, email, password)
        u.first_name = first_name
        u.last_name = last_name
        u.save()
        contact = Contact(first_name=first_name, last_name=last_name, email=email, role="Customer", user=u)
        contact.save()
        t = loader.get_template('email/welcome.txt')
        c = Context({
            'first_name': data['first_name'],
            'last_name' : data['last_name'],  
            'user_name': user_name })
        shop_config = Config.objects.get(site=settings.SITE_ID)
        shop_email = shop_config.storeEmail
        subject = "Welcome to %s" % (shop_config.storeName)
        c['company_name'] = shop_config.storeName
        c['login_url'] = "http://%s%s/account/login" % (shop_config.site.domain, settings.SHOP_BASE)
        send_mail(subject, t.render(c), shop_email,
                     [email], fail_silently=False)
    
    
def create(request):
    manipulator = AccountManipulator(request)
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            data = request.POST.copy()
            manipulator.save(data)
            user = authenticate(username=data['email'], password=data['password'])
            login(request, user)
            contact = Contact.objects.get(user=user.id)
            request.session['custID'] = contact.id
            return http.HttpResponseRedirect('%s/account/thankyou' % (settings.SHOP_BASE))
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('account_create_form.html', {'form': form},
                                RequestContext(request))

def info(request):
    try:
        user_data = Contact.objects.get(user=request.user.id)
    except:
        #This case happens if a user is created in admin but does not have account info
        return bad_or_missing(request, 'The person you are logged in as, does not have an account.  Please create one.')
    return render_to_response('account.html', {'user_data': user_data},
                              RequestContext(request))

_deco = user_passes_test(lambda u: not u.is_anonymous() ,
                        login_url='%s/account/login/' % (settings.SHOP_BASE))
info = _deco(info)

def shop_logout(request):
    logout(request)
    return http.HttpResponseRedirect('%s/' % (settings.SHOP_BASE))