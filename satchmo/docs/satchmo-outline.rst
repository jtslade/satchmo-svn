=====================
Satchmo documentation
=====================

Table of Contents
-----------------

- Introduction
    - History
    - Project mission
    - Features
    - Development Status
    
- Requirements

- Installation
    - Django installation
    - Getting source
    - Testing it

- Basic configuration
    - Loading data
    - Site specific configs

- Setting up your store
    - Loading products

- Framework design
    - Description of the models
        - Contact
        - Discount
        - Payment
        - Product
        - Shipping
        - Shop
        - Supplier
        - Thumbnails
    - Templates
    - Static information

- Roadmap
    
Introduction
------------

History
~~~~~~~
Like most Open Source projects, Satchmo was started to "scratch an itch."  This
particular itch was to create a framework for developing shopping cart software
using the Django framework.  After a little bit of discussion on the Django list, 
we created our own project in April 2006.

Project Mission
~~~~~~~~~~~~~~~
Satchmo's mission is to use Django to create an open source framework for creating 
unique and robust online stores. To provide maximum flexibility, Satchmo is licensed 
under the BSD license.

Features
~~~~~~~~

Current Development Status
~~~~~~~~~~~~~~~~~~~~~~~~~~
Satchmo is currently in alpha status.  Many functions work but there is still a lot
of change in the underlying api.

Requirements
------------
Satchmo is based on the Django framework, therefore you do need a fully functioning 
Django instance to use Satchmo.  The Django installation guide will step you 
through the process - http://www.djangoproject.com/documentation/install/

There are a number of other Python packages that are required for usage of all the 
features in Satchmo.

- Python Imaging Library
- Elementtree (included in Python 2.5+)
- Python cryptography toolkit
- Reportlab

Installation
------------
This guide assumes that Django is properly installed and that you have installed the
dependencies mentioned in the Requirements section.