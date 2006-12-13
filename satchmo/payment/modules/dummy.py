"""
This is a stub and used as the default processor.
It doesn't do anything but it can be used to build out another
interface.

See the authorizenet module for the reference implementation
"""

class PaymentProcessor(object):
    
    def __init__(self):
        pass
        
    def prepareData(self, data):
        pass
        
    def process(self):
        # Do some processing here
        
        reason_code = "0"
        response_text = "Success"
        
        return (True, reason_code, response_text)