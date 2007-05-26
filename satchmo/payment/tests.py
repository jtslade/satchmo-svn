# -*- coding: UTF-8 -*-
from django.test import TestCase
from satchmo.payment.paymentsettings import PaymentSettings
from django.core import urlresolvers

class TestModulesSettings(TestCase):

    def setUp(self):
        self.dummy = PaymentSettings().DUMMY
    
    def testGetDummy(self):
        self.assert_(self.dummy != None)
        self.assertEqual(self.dummy.label, 'Dummy processor')
            
    def testLookupTemplateSet(self):
        t = self.dummy.lookup_template('test.html')
        self.assertEqual(t, 'test.html')
        
        self.dummy['TEMPLATE_OVERRIDES'] = {'test2.html' : 'foo.html'}
        t = self.dummy.lookup_template('test2.html')
        self.assertEqual(t, 'foo.html')
        
    def testLookupURL(self):
        try:
            t = self.dummy.lookup_url('test_doesnt_exist')
            self.fail('Should have failed with NoReverseMatch')
        except urlresolvers.NoReverseMatch:
            pass
        
    def testLoad(self):
        module = self.dummy.load_processor()
        p = module.PaymentProcessor(self.dummy)
        result, reason, response = p.process()
        self.assertTrue(result)
        self.assertEqual(reason, "0")
        
    def testModuleName(self):
        self.assertEqual(self.dummy.make_modulename('urls'), 'satchmo.payment.modules.dummy.urls')
        
    def testUrlPatterns(self):
        pats = PaymentSettings().urlpatterns()
        self.assertTrue(len(pats) > 0)