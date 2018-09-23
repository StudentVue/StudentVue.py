import requests
from bs4 import BeautifulSoup

from urllib.parse import urlparse


class StudentVue:
    def __init__(self, username, password, districtdomain):
        """The StudentVue scraper object.
        Args:
            username (str): The username of the student portal account
            password (str): The password of the student portal account
            districtdomain (str): The domain name of your student portal
        """
        self.districtdomain = urlparse(districtdomain).netloc if urlparse(
            districtdomain).netloc else urlparse(districtdomain).path

        self.session = requests.Session()

        login_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_Login_Student.aspx?regenerateSessionId=True'.format(self.districtdomain)).text, 'html.parser')

        form = login_page.find(id='aspnetForm')

        form_data = {k: v for (k, v) in zip([input_['name'] for input_ in form.find_all(
            'input')], [input_.get('value', None) for input_ in form.find_all('input')])}

        form_data['ctl00$MainContent$username'] = username
        form_data['ctl00$MainContent$password'] = password

        resp = self.session.post('https://{}/PXP2_Login_Student.aspx?regenerateSessionId=True'.format(
            self.districtdomain), data=form_data)

        if resp.url != 'https://{}/Home_PXP2.aspx'.format(self.districtdomain):
            raise ValueError('Incorrect Username or Password')
