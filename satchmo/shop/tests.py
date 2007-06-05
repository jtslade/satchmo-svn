from django.test import TestCase
from django.test.client import Client
from django.core import mail
from django.utils.translation import gettext
from django.conf import settings

prefix = settings.SHOP_BASE

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
        response = self.client.get(prefix+'/')

        # Check that the rendered context contains 4 products
        self.assertContains(response, '<div class = "productImage">', 
                            count=4, status_code=200)
    
    def test_contact_form(self):
        """
        Validate the contact form works
        """
        
        response = self.client.get(prefix+'/contact/')
        self.assertContains(response, '<h3>Contact Information</h3>', 
                            count=1, status_code=200)
        response = self.client.post(prefix+'/contact/', {'name': 'Test Runner',
                              'sender': 'Someone@testrunner.com',
                              'subject': 'A question to test',
                              'inquiry': 'General Question',
                              'contents': 'A lot of info goes here.'})    
        self.assertRedirects(response, prefix+'/contact/thankyou/', status_code=302, target_status_code=200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'A question to test')
        
    def test_new_account(self):
        """
        Validate account creation process
        """
        response = self.client.get(prefix+'/account/create/')
        self.assertContains(response, "Please Enter Your Account Information", 
                            count=1, status_code=200)
        response = self.client.post(prefix+'/account/create/', {'email': 'someone@test.com',
                                    'first_name': 'Paul',
                                    'last_name' : 'Test',
                                    'password' : 'pass1',
                                    'password2' : 'pass1'})
        self.assertRedirects(response, prefix+'/account/thankyou/', status_code=302, target_status_code=200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Welcome to My Site')
        
        response = self.client.get(prefix+'/account/info/')
        self.assertContains(response, "Welcome, Paul Test.", count=1, status_code=200)

    def test_cart_adding(self):
        """
        Validate we can add some items to the cart
        """
        response = self.client.get(prefix+'/product/DJ-Rocks/')
        self.assertContains(response, "Django Rocks shirt", count=1, status_code=200)
        response = self.client.post(prefix+'/cart/1/add/', {"1" : "L",
                                                      "2" : "BL",
                                                      "quantity" : 2})
        self.assertRedirects(response, prefix+'/cart/', status_code=302, target_status_code=200)
        response = self.client.get(prefix+'/cart/')
        self.assertContains(response, "Django Rocks shirt ( Large/Blue )", count=1, status_code=200)
        
    def test_cart_removing(self):
        """
        Validate we can remove an item
        """
        self.test_cart_adding()
        response = self.client.get(prefix+'/cart/1/remove/')
        self.assertRedirects(response, prefix+'/cart/', status_code=302, target_status_code=200)
        response = self.client.get(prefix+'/cart/')
        #print response.content
        self.assertContains(response, "Your cart is currently empty.", count=1, status_code=200)
        
    def test_checkout(self):
        """
        Run through a full checkout process
        """
        self.test_cart_adding()
        #response = self.client.get(prefix+"/checkout/")
        response = self.client.post(prefix+"/checkout/", {'email': 'sometester@example.com',
                                    'first_name': 'Teddy',
                                    'last_name' : 'Tester',
                                    'phone': '456-123-5555',
                                    'street1': '8299 Some Street',
                                    'city': 'Springfield',
                                    'state': 'MO',
                                    'postalCode': '81122',
                                    'country': 'US',
                                    'ship_street1': '1011 Some Other Street',
                                    'ship_city': 'Springfield',
                                    'ship_state': 'MO',
                                    'ship_postalCode': '81123',
                                    'paymentmethod': 'DUMMY'})
        self.assertRedirects(response, prefix+'/checkout/dummy/', status_code=302, target_status_code=200)
        response = self.client.post(prefix+"/checkout/dummy/", {'credit_type': 'Visa',
                                    'credit_number': '4485079141095836',
                                    'month_expires': '1',
                                    'year_expires': '2009',
                                    'ccv': '552',
                                    'shipping': 'FlatRate'})
        self.assertRedirects(response, prefix+'/checkout/dummy/confirm/', status_code=302, target_status_code=200)
        response = self.client.get(prefix+'/checkout/dummy/confirm/')
        self.assertContains(response, "Total = $54.50", count=1, status_code=200)
        self.assertContains(response, "Shipping + $5.00", count=1, status_code=200)
        self.assertContains(response, "Tax + $3.50", count=1, status_code=200)
        response = self.client.post(prefix+"/checkout/dummy/confirm/", {'process' : 'True'})
        self.assertRedirects(response, prefix+'/checkout/dummy/success/', status_code=302, target_status_code=200)
        self.assertEqual(len(mail.outbox), 1)
       
