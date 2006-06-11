"""
Each payment option needs to define a method to display the required data entry fields
as well as validate and store the payment

This verification code was lightly modified from here -
http://py.vaults.ca/parnassus/apyllo.py/812237977.281773030.7554750.28824358
Thanks to Sean Reifschneider (jafo@tummy.com) for the original validation work.
"""

ccInfo = (
	#  type, prefix, length
	( 'Visa', '4', 16),
	( 'Visa', '4', 13),
	( 'Mastercard', '51', 16),
	( 'Mastercard', '52', 16),
	( 'Mastercard', '53', 16),
	( 'Mastercard', '54', 16),
	( 'Mastercard', '55', 16),
	( 'Discover', '6011', 16),
	( 'American Express', '34', 15),
	( 'American Express', '37', 15),
	( 'Diners Club/Carte Blanche', '300', 14),
	( 'Diners Club/Carte Blanche', '301', 14),
	( 'Diners Club/Carte Blanche', '302', 14),
	( 'Diners Club/Carte Blanche', '303', 14),
	( 'Diners Club/Carte Blanche', '304', 14),
	( 'Diners Club/Carte Blanche', '305', 14),
	( 'Diners Club/Carte Blanche', '36', 14),
	( 'Diners Club/Carte Blanche', '38', 14),
	( 'JCB', '3', 16),
	( 'JCB', '2131', 15),
	( 'JCB', '1800', 15),
	)

class CreditCard(object):
        
    def __init__(self, number, ccv, expiry, cardtype):
        self.card_number = number
        self.card_expiry = expiry
        self.card_CCV = ccv
        self.card_type = cardtype
    
    def _verifyMod10(self, number):
        '''Check a credit card number for validity using the mod10 algorithm. '''
        double = 0
        sum = 0
        for i in range(len(number) - 1, -1, -1):
            for c in str((double + 1) * int(number[i])): sum = sum + int(c)
            double = (double + 1) % 2
        return((sum % 10) == 0)
    
    
    def _stripCardNum(self, card):
        '''Return card number with all non-digits stripped.  '''
        import re
        return(re.sub(r'[^0-9]', '', self.card_number))

    def verifyCardNumber(self):
        '''Return card type string if legal, None otherwise.
        Check the card number and return a string representing the card type if
        it could be a valid card number.

        RETURNS: (String) Credit card type string if legal.(None) if invalid.
        '''
        s = self._stripCardNum(self.card_number)
        for name, prefix, length in ccInfo:
            if len(s) == length and s[:len(prefix)] == prefix:
                if self._verifyMod10(s):
                    return(name)
                break
        return(None)
    
    def __str__(self):
        return("Credit Card Payment")
        
    def RenderForm(self):
        pass
        
    def ProcessPayment(self, CustomerOrder):
        """
        Take all the info from the order, populate the fields we need, connect to authorize.net
        and pay for the product.  Return a status code letting the user know what worked.
        """
        pass
        