import re
import json


def parse_data_grid(script):
    match = re.search(r'new DevExpress.PXPRemoteDataStore\(\'([A-Z0-9-]+)\', \'({.+})\'\)', script)
    return match.group(1), json.loads(match.group(2))


def parse_form(form):
    keys = [input_['name'] for input_ in form.find_all('input')] + \
           [select['name'] for select in form.find_all('select')]
    values = [input_.get('value', None) for input_ in form.find_all('input')] + \
             [select.find('option', selected='selected').get('value', None) for select in form.find_all('select')]
    return {k: v for (k, v) in zip(keys, values)}


# parses out an email, with tolerance for javascript: links
def parse_email(text):
    match = re.search(r'([a-zA-z0-9]+@[a-zA-z]+.[a-zA-z]+)', text)
    return match.group(1) if match else text
