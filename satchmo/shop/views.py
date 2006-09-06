# Create your views here.

from django.shortcuts import render_to_response
from django.contrib.auth.decorators import user_passes_test
from django import http
from django.template import RequestContext, Context
from django.template import loader
from satchmo.product.models import Item, Category, OptionItem
from satchmo.shop.models import Cart, CartItem, Config
from sets import Set
from django.conf import settings
from django.contrib.auth import logout, login, authenticate
from django import forms
from django.core import validators
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from satchmo.contact.models import Contact

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


def contact_form(request):
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
            new_data['name'] = Contact.objects.filter(user=request.user.id)[0].full_name
            errors = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('contact_form.html', {'form': form},
                                RequestContext(request))


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
            forms.TextField(field_name="user_name",length=30, is_required=True),
        )
        
    def isValidPassword(self, field_data, all_data):
        if not (field_data == all_data['password']):
            raise validators.ValidationError("Your passwords do not match.")
    
    def isUniqueEmail(self, field_data, all_data):
        if User.objects.filter(email=field_data).count() > 0:
            raise validators.ValidationError("That email address already exists.")
    
    def save(self, data):
        user_name = data['user_name']
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
            'user_name': data['user_name'] })
        shop_config = Config.objects.get(site=settings.SITE_ID)
        shop_email = shop_config.storeEmail
        subject = "Welcome to %s" % (shop_config.storeName)
        c['company_name'] = shop_config.storeName
        c['login_url'] = "http://%s%s/account/login" % (shop_config.site.domain, settings.SHOP_BASE)
        send_mail(subject, t.render(c), shop_email,
                     [email], fail_silently=False)
    
    
def account_create(request):
    manipulator = AccountManipulator(request)
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            data = request.POST.copy()
            manipulator.save(data)
            user = authenticate(username=data['user_name'], password=data['password'])
            login(request, user)
            return http.HttpResponseRedirect('%s/account/thankyou' % (settings.SHOP_BASE))
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('account_create_form.html', {'form': form},
                                RequestContext(request))

def bad_or_missing(request, msg):
    """
    Return an HTTP 404 response for a date request that cannot possibly exist.
    The 'msg' parameter gives the message for the main panel on the page.
    """
    template = loader.get_template('shop_404.html')
    context = RequestContext(request, {'message': msg})
    return http.HttpResponseNotFound(template.render(context))

        
def category_root(request, slug):
    #Display the category page if we're not dealing with a child category
    try:
        category = Category.objects.filter(slug=slug)[0]
    except IndexError:
        return bad_or_missing(request, 'The category you have requested does '
            'not exist.')
    return render_to_response('base_category.html',{'category':category},
                                RequestContext(request))

def category_children(request, slug_parent, slug):
    #Display the category if it is a child
    try:
        parent = Category.objects.filter(slug=slug_parent)[0]
    except IndexError:
        return bad_or_missing(request, 'The category you have requested does '
            'not exist.')
    try:
        category = parent.child.filter(slug=slug)[0]
    except IndexError:
        return bad_or_missing(request, 'The category you have requested does '
            'not exist.')
            
    return render_to_response('base_category.html',{'category':category}, 
                                RequestContext(request))

def display_cart(request):
    #Show the items in the cart
    cart_list = []
    total = 0
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        total = tempCart.total
        return render_to_response('base_cart.html', {'all_items': tempCart.cartitem_set.all(),
                                                       'total': total},
                                                        RequestContext(request))
    else:
        return render_to_response('base_cart.html', {'all_items' : [],
                                                        'total':total},
                                                        RequestContext(request))

def add_to_cart(request, id):
    #Todo: Error checking for invalid combos
    #Add an item to the session/cart
    chosenOptions = Set()
    price_delta = 0
    try:
        product = Item.objects.get(pk=id)
    except Item.DoesNotExist:
        return bad_or_missing(request, 'The product you have requested does '
                'not exist.')
    for option in product.option_group.all():
        chosenOptions.add('%s-%s' % (option.id,request.POST[str(option.id)]))
        #print '%s-%s' % (option.id,request.POST[str(option.id)])
    try:
        quantity = int(request.POST['quantity'])
    except ValueError:
        return render_to_response('base_product.html', {
            'item': product,
            'error_message': "Please enter a whole number"},
             RequestContext(request))
    if quantity < 0:
        return render_to_response('base_product.html', {
            'item': product,
            'error_message': "Negative numbers can not be entered"},
             RequestContext(request))
    #Now get the appropriate sub_item
    chosenItem = product.get_sub_item(chosenOptions)
    #If we get a None, then there is not a valid subitem so tell the user
    if not chosenItem:
        return render_to_response('base_product.html', {
            'item': product,
            'error_message': "Sorry, this choice is not available."},
             RequestContext(request))
                
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
    else:
        tempCart = Cart()
    tempCart.save() #need to make sure there's an id
    tempCart.add_item(chosenItem, number_added=quantity)
    request.session['cart'] = tempCart.id

    return http.HttpResponseRedirect('%s/cart' % (settings.SHOP_BASE))

def remove_from_cart(request, id):
    tempCart = Cart.objects.get(id=request.session['cart'])
    if request.has_key('quantity'):
        quantity = request.POST['quantity']
    else:
        quantity = 9999
    tempCart.remove_item(id, quantity)
    return http.HttpResponseRedirect('%s/cart' % (settings.SHOP_BASE))

def account_info(request):
    user_data = Contact.objects.filter(user=request.user.id)[0]
    return render_to_response('account.html', {'user_data': user_data},
                              RequestContext(request))
                              
_deco = user_passes_test(lambda u: not u.is_anonymous() ,
                        login_url='%s/account/login/' % (settings.SHOP_BASE))
account_info = _deco(account_info)

def account_logout(request):
    logout(request)
    return http.HttpResponseRedirect('%s/' % (settings.SHOP_BASE))