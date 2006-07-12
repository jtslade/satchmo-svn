"""
This file is used to prepopulate country information into the tables.
If you wish to modify data, modify the ./data/countries.csv file
"""
import csv
from satchmo.localization.models import *
print "Loading countries...."
reader = csv.reader(open(r"./data/countries.csv","rb"))

reader.next() #Skip the header

for row in reader:
    country = Country(name = row[0], alpha2_code = row[1], zone = row[2], 
                      int_dialcode = row[3])
    if row[4]:
        country.main_subdiv = row[4]
    country.save()
print "Done!"