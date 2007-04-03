# This file is used to store your site specific settings
# for database access.
# It also store satchmo unique information
#
#
# Modify this file to reflect your settings, then rename it to 
# local_settings.py
#
# This file is helpful if you have an existing Django project.  
# These are specific things that Satchmo will need.
# you MUST make sure these settings are imported from your project settings file!

import os
import logging
DIRNAME = os.path.dirname(__file__)

# This is useful, since satchmo is not the "current directory" like load_data expects.
# SATCHMO_DIRNAME = ''

# Only set these if Satchmo is part of another Django project
#SITE_NAME = ''
#ROOT_URLCONF = ''
#MEDIA_ROOT = os.path.join(DIRNAME, 'static/')
#DJANGO_PROJECT = 'Your Main Project Name'
#DJANGO_SETTINGS_MODULE = 'main-project.settings'

# Make sure Satchmo templates are added to your existing templates
# TEMPLATE_DIRS += (
#    os.path.join(SATCHMO_DIRNAME, "templates"),
#)

# Make sure Satchmo context processor is called
# TEMPLATE_CONTEXT_PROCESSORS += ('satchmo.shop.context_processors.settings')

DATABASE_NAME = ''
DATABASE_PASSWORD = ''
DATABASE_USER = ''
SECRET_KEY = ''

#### For Authorize.net ######
#AUTHORIZE_NET_CONNECTION = 'https://test.authorize.net/gateway/transact.dll'
#AUTHORIZE_NET_TEST = 'TRUE'
#AUTHORIZE_NET_LOGIN = ''
#AUTHORIZE_NET_TRANKEY = ''

#### Satchmo unique variables ####
#This is the base url for the shop.  Only include a leading slash
#examples: '/shop' or '/mystore'
#If you want the shop at the root directory, set SHOP_BASE = ''
SHOP_BASE = '/shop'

# Currency symbol to use
CURRENCY = '$'

#These are used when loading the test data
SITE_DOMAIN = "example.com"
SITE_NAME = "My Site"

#Configure logging
LOGDIR = "/path/to/log"
LOGFILE = "satchmo.log"
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=os.path.join(LOGDIR, LOGFILE),
                    filemode='w')

# define a Handler which writes INFO messages or higher to the sys.stderr
fileLog = logging.FileHandler(os.path.join(LOGDIR, LOGFILE), 'w')
fileLog.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
fileLog.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(fileLog)
logging.info("Satchmo Started")
