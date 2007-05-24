from django.test import TestCase
from django.test.client import Client
from django.core import mail
from django.utils.translation import gettext

class ShopTest(TestCase):
    fixtures = ['i18n-data.yaml', 'sample-store-data.yaml']
    
    def setUp(self):
        # Every test needs a client
        self.client = Client()
        __builtins__['_'] = gettext
    
    def test_main_page(self):
        """
        Look at the main page
        """
        response = self.client.get('/')

        # Check that the rendered context contains 4 products
        self.assertContains(response, '<div class = "productImage">', 
                            count=4, status_code=200)
    
    def test_contact_form(self):
        """
        Validate the contact form works
        """
        
        response = self.client.get('/contact/')
        self.assertContains(response, '<h3>Contact Information</h3>', 
                            count=1, status_code=200)
        response = self.client.post('/contact/', {'name': 'Test Runner',
                              'sender': 'Someone@testrunner.com',
                              'subject': 'A question to test',
                              'inquiry': 'General Question',
                              'contents': 'A lot of info goes here.'})    
        self.assertRedirects(response, '/contact/thankyou/', status_code=302, target_status_code=200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'A question to test')
        
    def test_new_account(self):
        """
        Validate account creation process
        """
        response = self.client.get('/account/create/')
        self.assertContains(response, "Please Enter Your Account Information", 
                            count=1, status_code=200)
        response = self.client.post('/account/create/', {'email': 'someone@test.com',
                                    'first_name': 'Paul',
                                    'last_name' : 'Test',
                                    'password' : 'pass1',
                                    'password2' : 'pass1'})
        self.assertRedirects(response, '/account/thankyou/', status_code=302, target_status_code=200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Welcome to My Site')
        
        response = self.client.get('/account/info/')
        self.assertContains(response, "Welcome, Paul Test.", count=1, status_code=200)

    def test_cart_adding(self):
        """
        Validate we can add some items to the cart
        """
        response = self.client.get('/product/DJ-Rocks/')
        self.assertContains(response, "Django Rocks shirt", count=1, status_code=200)
        response = self.client.post('/cart/1/add/', {"1" : "L",
                                                      "2" : "BL",
                                                      "quantity" : 2})
        self.assertRedirects(response, '/cart/', status_code=302, target_status_code=200)
        response = self.client.get('/cart/')
        self.assertContains(response, "Django Rocks shirt ( Large/Blue )", count=1, status_code=200)
