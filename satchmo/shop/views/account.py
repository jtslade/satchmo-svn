from django import http
from django import newforms as forms
from django.conf import settings
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render_to_response
from django.template import loader
from django.template import RequestContext, Context
from django.utils.translation import gettext_lazy as _
from satchmo.contact.models import Contact
from satchmo.shop.models import Config
from satchmo.shop.utils.unique_id import generate_id
from satchmo.shop.views.utils import bad_or_missing

class AccountForm(forms.Form):
    """The basic account form."""
    # user_name = forms.CharField(label=_('User Name'), max_length=30, required=True)
    email = forms.EmailField(label=_('Email'), max_length=30, required=True)
    password2 = forms.CharField(label=_('Password (again)'), max_length=30, widget=forms.PasswordInput(), required=True)
    password = forms.CharField(label=_('Password'), max_length=30, widget=forms.PasswordInput(), required=True)
    first_name = forms.CharField(label=_('First Name'), max_length=30, required=True)
    last_name = forms.CharField(label=_('Last Name'), max_length=30, required=True)

    
    def clean_password(self):
        """Enforce that password and password2 are the same."""
        p1 = self.cleaned_data.get('password', None)
        p2 = self.cleaned_data.get('password2', None)
        if not(p1 and p2 and p1 == p2):
            raise forms.ValidationError("The two passwords do not match." )

        # note, here is where we'd put some kind of custom validator to enforce "hard" passwords.
        return p1    

    def clean_email(self):
        """Prevent account hijacking by disallowing duplicate emails."""
        email = self.cleaned_data.get('email', None)
        if email and User.objects.filter(email=email).count() > 0:
            raise forms.ValidationError("That email address is already in use.")
        
        return email
    
    #### Not currently used.  Preserved during conversion to newforms.    
    # def test_unique_username(self):
    #     """Test to ensure that the username is not already used."""
    #     username = self.cleaned_data.get('user_name', None)
    #     if username and User.objects.filter(username=username).count() > 0:
    #         raise forms.ValidationError("That username already exists.")
    
    def save(self):
        """Save the user object, returning it."""
        
        user = None
        if self.is_valid():
            data = self.cleaned_data

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
            c['login_url'] = "http://%s%s/account/login/" % (shop_config.site.domain, settings.SHOP_BASE)
            send_mail(subject, t.render(c), shop_email,
                         [email], fail_silently=False)
                         
        return u    
    
    
def create(request):
    if request.method == "POST":
        form = AccountForm(request.POST)
        if form.is_valid():
            user = form.save()
            data = form.cleaned_data
            user = authenticate(username=user.username, password=data['password'])
            login(request, user)
            contact = Contact.objects.get(user=user.id)
            request.session['custID'] = contact.id
            
            return http.HttpResponseRedirect('%s/account/thankyou/' % (settings.SHOP_BASE))

    else:
        form = AccountForm()
            
    ctx = RequestContext(request, {'form': form})
    return render_to_response('account_create_form.html', ctx)


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
