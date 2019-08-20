import re


def parse_form(form):
    return {k: v for (k, v) in zip([input_['name'] for input_ in form.find_all(
            'input')], [input_.get('value', None) for input_ in form.find_all('input')])}


# parses out an email, with tolerance for javascript: links
def parse_email(text):
    match = re.search(r'([a-zA-z0-9]+@[a-zA-z]+.[a-zA-z]+)', text)
    return match.group(1) if match else text
