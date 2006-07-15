import csv
import glob
import os
import re
import sys

from satchmo.localization.models import *


"""
Country
-------
The USPS primary destinations are formed by the country code, a dot,
and a code invented fot that localization. Setting off 'display'

"""

# Configuration
# ---------------------------------------------------------------------- #
DATA_DIR = "./data"  # CSV files.
MODELS_FILE = "./localization/models.py"

# Countries unhabitted or with a very few habitants. Setting off 'display'
UNHABITTED = ['AQ', 'BV', 'HM', 'PN', 'GS', 'UM']
# ---------------------------------------------------------------------- #


def get_data_models():
    '''Get the name of all models and fields.
Add '#' character after of field name if is numeric.
    '''
    global FULL_MODELS
    FULL_MODELS = []
    model_data = []
    re_field = re.compile('\s+\w+\s*=\s*models\.')  # Line with field name
    re_class = re.compile('\s+class ')  # For Admin and Meta
    re_def = re.compile('\s+def ')
    is_new_model = False

    for line in open(MODELS_FILE):
        # The models start with 'class'
        if not is_new_model and line.startswith('class'):
            FULL_MODELS.append(model_data)
            model_name = line.replace('class','').split('(')[0].strip()
            model_data.append(model_name)
            is_new_model = True
        elif is_new_model:
            if re_field.match(line):
                field_name = line.split('=')[0].strip()
                model_data.append(field_name)
                if 'models.FloatField' in line or 'IntegerField' in line:
                    model_data.append('#')  # To indicating that is numeric.
            elif re_class.match(line) or re_def.match(line):
                model_data = []
                is_new_model = False


def load_data(csv_file):
    '''Get the fields position where there are numbers.
    '''
    global FULL_MODELS
    position_num = []  # Store the position of numeric fields
    fields = []  # Fields name of model
    re_int = re.compile('\d+$')  # An integer number
    csv_separator = ':'  # Separator used in CSV data

    # Get data from CSV header.
    # The model is separated of the fields by ':'
    first_line = open(csv_file).readline().split(':')
    model = first_line[0].strip()
    for field in first_line[-1].split(','):  # Fields separated by ','
        fields.append(field.strip())
    fields_number = len(fields)

    # Check that names in CSV header are correct, and check numeric fields.
    data_found = False
    for data_model in FULL_MODELS:
        if data_model[0] == model:
            len_data_model = len(data_model) - 1
            for field in fields:
                if field not in data_model:
                    sys.exit("Error in file '%s'. \
Field name '%s' is not correct." % (csv_file, field))
                # Get the position of each field to check '#' (numeric field)
                else:
                    position = data_model.index(field)
                    # The position has to be lesser that length of list -1
                    if position < len_data_model and \
                      data_model[position+1] == '#':
                        position = fields.index(field)
                        position_num.append(position)

            data_found = True
            break

    if not data_found:
        sys.exit("Error in file '%s'. Model name '%s' is not correct." \
               % (csv_file, model))

    # Convert from CSV to Django ORM
    reader = csv.reader(open(csv_file), delimiter=csv_separator)
    reader.next()  # Skip the header

    line_number = 0
    for csv_line in reader:
        object_line = []
        line_number += 1
        object_line.append("c%d = %s(" % (line_number, model))

        for position in range(0, fields_number):
            if csv_line[position]:
                if not object_line[-1].endswith('('):
                    object_line.append(', ')

                if position in position_num:  # If the field is an integer
                    object_line.append('%s=%s' \
                        % (fields[position], csv_line[position]))
                else:
                    object_line.append('%s="%s"' \
                        % (fields[position], csv_line[position]))

        object_line.append(")")
        load_object = ''.join(object_line)
        exec(load_object)  # Load the object
#        print load_object

    # At the end, save all objects together
    print "Creating %s objects ..." % model
    for num in range(1, line_number+1):
        obj = eval('c%d' % num)
        if model == 'Country':
            if obj.alpha2_code in UNHABITTED or '.' in obj.alpha2_code:
                obj.display = False
        obj.save()


def main():
    '''Prepopulate the information from CSV data into tables.

If you wish to modify data, modify the files in 'DATA_DIR' directory.

The header format in the CSV files has to be:
[Model name]: [field 1] [, field 2, ... field n]
    '''
    get_data_models()

    try:
        os.chdir(DATA_DIR)
    except OSError, err:
        print "Error! %s: %r" % (err.strerror, err.filename)
        sys.exit(1)

    csv_files = glob.glob('*.csv')
    if not csv_files:
        sys.exit("Error! Not found CSV files.")

    for csv in csv_files:
        load_data(csv)


if __name__ == '__main__':
    main()
