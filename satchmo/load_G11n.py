import csv
import glob
import os
import re
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = "satchmo.settings"
from satchmo.G11n.models import *


def get_data_models(models_file):
    '''Get the name of all models and fields.
And add information about numeric fields and keys.

The numeric fields have as format:
#[numeric X position]...

And the keys:
:K-[num. pos. of key],[model related]
    '''
    list_models = []
    model = []
    pos_numeric = []  # Position of numeric fields
    info_keys = []  # Info. about keys
    re_field = re.compile('\s+\w+\s*=\s*models\.')  # Line with field name
    re_class = re.compile('\s+class ')  # For Admin and Meta
    re_def = re.compile('\s+def ')
    is_new_model = False

    for line in open(models_file):
        # The models start with 'class'
        if not is_new_model and line.startswith('class'):
            model_name = line.replace('class','').split('(')[0].strip()
            model.append(model_name)
            is_new_model = True
        elif is_new_model:
            if re_field.match(line):
                field_name = line.split('=')[0].strip()
                model.append(field_name)

                if 'models.FloatField' in line or 'IntegerField' in line:
                    pos_numeric.append(len(model)-2)  # Discard model name.
                elif 'models.ForeignKey' in line:
                    key_name = line.split('(')[-1].strip().strip(')')
                    position = len(model)-2  # Discard model name.
                    info_keys.append(':')
                    info_keys.append(str(position) + ',')
                    info_keys.append(key_name)
            # It is supposed that models in localization has at the end:
            # ('class Meta', 'class Admin', or some 'def')
            elif re_class.match(line) or re_def.match(line):
                if pos_numeric:
                    pos_num2str = '#'
                    for num in pos_numeric:
                        pos_num2str += str(num)
                    model.append(pos_num2str)
                    model.append(':N')  # To detect the numeric field.
                    pos_numeric = []
                if info_keys:
                    all_keys = ""
                    for key in info_keys:
                        all_keys += key
                    model.append(all_keys)
                    model.append(':K')  # To detect fastly some key.
                    info_keys = []
                list_models.append(model)
                model = []
                is_new_model = False

    return list_models


def sort_models(data_dir, list_models):
    '''The models with keys (foreign, etc) go at the end.
    '''
    list_new_models = []  # Only left fields in CSV file.

    try:
        os.chdir(data_dir)
    except OSError, err:
        print "Error! %s: %r" % (err.strerror, err.filename)
        sys.exit(1)

    csv_files = glob.glob('*.csv')
    if not csv_files:
        sys.exit("Error! Not found CSV files.")

    for csv in csv_files:
        list_new_models.append(check_header(csv, list_models))

    for model in list_new_models[:]:
        # Put models with ForeignKey in the last positions
        if ':K' in model and \
          list_new_models.index(model) < len(list_new_models)-1:
            list_new_models.append(model)
            list_new_models.remove(model)

    return list_new_models


def check_header(csv_file, list_models):
    '''Get and check data from CSV header, create a new list of models and
insert the file CSV name in model line.

Format: * code: [Model name], [field name 1], ... [field name n]*
    '''
    new_model = []
    line_found = False
    full_line = False

    # Get line with info. about model.
    for line in open(csv_file):
#        if line[:1] == '#':  #  For use in list of strings
        if line[0] == '#':
            if not line_found and '* code:' in line:
                code_line = line.split(':')[-1]
                line_found = True
            elif line_found:
                if not '*' in code_line:
                    code_line += line
                else:
                    full_line = True
                    break
        else:
            break

    if not line_found:
        sys.exit("Code line not found in '%s'." % csv_file)
    if not full_line:
        sys.exit("Code line not finished with '*' in '%s'." % csv_file)

    code_line = code_line.split('*')[0].replace('#','')
    # Fields name of model in CSV file separated by ','
    csv_fields = [ x.strip() for x in code_line.split(',') ]
    model = csv_fields[0]
    csv_fields.remove(csv_fields[0])

    # Check header and build new list.
    for data_model in list_models:
        if data_model[0] == model:  # Check model name.
            new_model.append(model)  # Add model name
            for field in csv_fields:
                if field in data_model:  # Check fields.
                    new_model.append(field)  # Add field.
                else:
                    sys.exit("Error in file '%s'. \
Field name '%s' is not correct." % (csv_file, field))

            # Insert name of CSV file
            new_model.insert(0, csv_file)
            # Insert both numeric and key fields
            new_model += [ x for x in data_model if '#' in x or ':' in x ]
            break

    if not new_model:
        sys.exit("Error in file '%s'. Model name '%s' is not correct." \
               % (csv_file, model))

    return new_model


def comment_stripper(iterator):
    '''Generator that filters comments and blank lines.

Used as input to 'cvs.reader'.
    '''
    for line in iterator:
        if line [:1] == '#':
            continue
        if not line.strip ():
            continue
        yield line


def load_data(model):
    '''Get the fields position where there are numbers.
    '''
    position_num = []
    dic_keys = {}
    csv_separator = ':'
    re_num = re.compile('\d+$')

    # Get only the fields name
    fields = [ x for x in model[2:] if not (':' in x or '#' in x) ]
    # Get left data.
    fields_number = len(fields)
    csv_file = model[0]
    model_name = model[1]
    print "Creating %s objects ..." % model_name

    # Get the position of numeric fields
    if ':N' in model:
        pos = model.index(':N')
        position_num = model[pos-1]  # The field numeric is before of ':N'
        position_num = [ int(x) for x in position_num if not '#' in x ]

    # Info. about keys
    if ':K' in model:
        pos = model.index(':K')
        info_keys = model[pos-1]
        # Format-> :[position],[model name]:...
        info_keys = info_keys.split(':')[1:]
        keys = [ (int(x.split(',')[0]), x.split(',')[1]) for x in info_keys ]
        dic_keys = dict(keys)

        # To store the keys. Set to values null
        model_id = {}
        for x in dic_keys.keys():
            model_id.setdefault(x, None)

    # Convert from CSV to Django ORM
    reader = csv.reader(comment_stripper(
                        open(csv_file)), delimiter=csv_separator)

    line_bool = []  # Lines where is enabled a boolean field.
    bool_found = False
    line_number = 0
    for csv_line in reader:
        #debug
#        if \
#        model_name == "Phone" or \
#        model_name == "AddressFormat":
#        model_name == "Country" or \
#        model_name == "CountryLanguage" or \
#        model_name == "Language" or \
#        model_name == "Subdivision" or \
#        model_name == "TimeZone" or
#            print "\tskip"
#            break

        object_line = []
        key_line_s = []
        line_number += 1
        object_line.append("c%d = %s(" % (line_number, model_name))
        for position in range(0, fields_number):
            field_text = csv_line[position]
            if field_text == 'True':
                if not bool_found:
                    bool_field = fields[position]
                    bool_found = True
                line_bool.append(line_number)
            elif field_text:  # If is not empty
                key_line = []
                if object_line[-1][-1] != '(':  # Check the last character
                    object_line.append(', ')
                # If is a key
                if dic_keys and dic_keys.has_key(position):
                    object_line.append('%s=key_id%d'
                                       % (fields[position], position))
                    key_model = dic_keys.get(position)

                    if csv_line[position] != model_id.get(position):
                        model_id[position] = csv_line[position]

                        key_line.append('key_id%d = %s.objects.get(pk='
                                        % (position, key_model))
                        if re_num.match(model_id.get(position)):  # integer
                            key_line.append('%d)' % model_id.get(position))
                        else:
                            key_line.append('"%s")' % model_id.get(position))

                        key_line = ''.join(key_line)
                        key_line_s.append(key_line)

                # If is an integer
                elif position in position_num:
                    object_line.append('%s=%s' \
                        % (fields[position], csv_line[position]))
                # If is a string.
                else:
                    object_line.append('%s="%s"' \
                        % (fields[position], csv_line[position]))

        if key_line_s:
            for key in key_line_s:
                exec(key)
#                print key #debug

        object_line.append(")")
        load_object = ''.join(object_line)
        exec(load_object)  # Load the object
#        print load_object #debug

    # At the end, save all objects together
    if model_name == 'Language':
        # Display the english language.
        for num in range(1, line_number+1):
            obj = eval("c%d" % num)
            if obj.alpha3_code == 'eng':
                obj.display = True
            obj.save()
    else:
        for num in range(1, line_number+1):
            obj = eval("c%d" % num)
            if num in line_bool:
                exec("obj.%s = True" % bool_field)
            obj.save()


def main():
    '''Prepopulate the information from CSV data into tables.

If you wish to modify data, modify the files in 'data_dir' directory.

The header format in the CSV files has to be:
* [Model name], [field 1] [, field 2, ... field n] *
    '''
    data_dir = "./G11n/data"  # CSV files.
    models_file = "./G11n/models.py"

    models = get_data_models(models_file)
    new_models = sort_models(data_dir, models)

    for model in new_models:
        load_data(model)


if __name__ == '__main__':
    main()
