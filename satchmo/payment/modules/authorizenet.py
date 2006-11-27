from urllib import urlencode
import urllib2
from django.conf import settings

class PaymentProcessor(object):
    #Authorize.NET payment processing module
    #You must have an account with authorize.net in order to use this module
    def __init__(self):
        self.connection = settings.AUTHORIZE_NET_CONNECTION
        self.contents = ''
        self.configuration = {
            'x_login' : settings.AUTHORIZE_NET_LOGIN,
            'x_tran_key' : settings.AUTHORIZE_NET_TRANKEY, 
            'x_version' : '3.1',
            'x_relay_response' : 'FALSE',
            'x_test_request' : settings.AUTHORIZE_NET_TEST,
            'x_delim_data' : 'TRUE',
            'x_delim_char' : '|',
            'x_type': 'AUTH_CAPTURE',
            'x_method': 'CC',                
            }
            
        
    def prepareData(self, data):
        self.custBillData = {
            'x_first_name' : data.contact.first_name,
            'x_last_name' : data.contact.last_name,
            'x_address': data.fullBillStreet,
            'x_city': data.billCity,
            'x_state' : data.billState,
            'x_zip' : data.billPostalCode,
            'x_country': data.billCountry,
            'x_phone' : data.contact.primary_phone
            }
        # Can add additional info here if you want to but it's not required
        self.transactionData = {
            'x_amount' : data.total,
            'x_card_num' : data.CC.decryptedCC,
            'x_exp_date' : data.CC.expirationDate,
            'x_card_code' : data.CC.ccv
            }
        
        self.postString = urlencode(self.configuration) + "&" + urlencode(self.transactionData) + "&" + urlencode(self.custBillData)
            
    def process(self):
        # Execute the post to Authorize Net
        print self.postString
        conn = urllib2.Request(url=self.connection, data=self.postString)
        f = urllib2.urlopen(conn)
        all_results = f.read()
        parsed_results = all_results.split(self.configuration['x_delim_char'])
        response_code = parsed_results[0]
        reason_code = parsed_results[1]
        response_text = parsed_results[3]
        #print all_results
        if response_code == '1':
            return(True, reason_code, response_text)
        elif response_code == '2':
            return(False, reason_code, response_text)
        else:
            return(False, reason_code, response_text)
  
        
if __name__ == "__main__":
    #####
    # This is for testing - enabling you to run from the command line & make sure everything is ok
    #####
    
    # Set up some dummy classes to mimic classes being passed through Satchmo
    class testContact(object):
        pass
    class testCC(object):
        pass
    class testOrder(object):
        def __init__(self):
            self.contact = testContact()
            self.CC = testCC()
    import os
    os.environ["DJANGO_SETTINGS_MODULE"]="satchmo.settings"
    settings_module = os.environ['DJANGO_SETTINGS_MODULE']
    settingsl = settings_module.split('.')
    settings = __import__(settings_module, {}, {}, settingsl[-1])
    
    sampleOrder = testOrder()
    sampleOrder.contact.first_name = 'Chris'
    sampleOrder.contact.last_name = 'Smith'
    sampleOrder.contact.primary_phone = '801-555-9242'
    sampleOrder.fullBillStreet = '123 Main Street'
    sampleOrder.billPostalCode = '12345'
    sampleOrder.billState = 'TN'
    sampleOrder.billCity = 'Some City'
    sampleOrder.billCountry = 'US'
    sampleOrder.total = "27.00"
    sampleOrder.CC.decryptedCC = '6011000000000012'
    sampleOrder.CC.expirationDate = "10/09"
    sampleOrder.CC.ccv = "144"

    processor = PaymentProcessor()
    processor.prepareData(sampleOrder)
    results, reason_code, msg = processor.process()
    print results,"::", msg
        
