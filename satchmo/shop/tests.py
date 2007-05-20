from django.test import TestCase
from django.test.client import Client
from django.core import mail

class SimpleTest(TestCase):
    fixtures = ['i18n-data.yaml', 'sample-store-data.yaml']
    
    def setUp(self):
        # Every test needs a client
        self.client = Client()
    
    def test_details(self):
        # Look at the main page
        response = self.client.get('/')

        # Check that the rendered context contains 4 products
        self.assertContains(response, '<div class = "productImage">', 
                            count=4, status_code=200)

        #Validate the contact form works
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