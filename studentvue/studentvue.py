import requests
from bs4 import BeautifulSoup

from urllib.parse import urlparse

import re

import studentvue.models as models


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

        home_page = BeautifulSoup(resp.text, 'html.parser')

        self.id_ = re.match(
            'ID: ([0-9]+)', home_page.find(class_='student-id').text.strip()).group(1)
        self.name = home_page.find(class_='student-name').text

        self.school_name = home_page.find(class_='school').text
        self.school_phone = home_page.find(class_='phone').text

        self.picture_url = 'https://{}/{}'.format(self.districtdomain,
                                                  home_page.find(alt='Student Photo')['src'])

    def getClasses(self):
        classes_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_Gradebook.aspx?AGU=0'.format(self.districtdomain)).text, 'html.parser')

        classes_table = classes_page.find('table')

        print(classes_table.find_all('tr', class_=False))

        return [
            models.Class(
                class_.find_all('td')[2].text,
                class_.find_all('td')[3].find('button').text,
                re.match('Room: ([a-zA-z0-9]+)', class_.find(class_='teacher-room').text.strip()).group(1),
                models.Teacher(
                    class_.find('div', class_='teacher').text,
                    re.search('([a-zA-z0-9]+@[a-zA-z]+.[a-zA-z]+)', class_.find('span', class_='teacher').find('a')['href']).group(1)
                ),
                float(class_.find(class_='score').text.replace('%', ''))
            ) for class_ in classes_table.find('tbody').find_all('tr', class_=False)
        ]
