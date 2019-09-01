import requests
from bs4 import BeautifulSoup

from urllib.parse import urlparse, parse_qs

from datetime import datetime
import json
import re

import studentvue.models as models
import studentvue.helpers as helpers


class StudentVue:
    def __init__(self, username, password, district_domain):
        """The StudentVue scraper object.
        Args:
            username (str): The username of the student portal account
            password (str): The password of the student portal account
            district_domain (str): The domain name of your student portal
        """
        self.district_domain = urlparse(district_domain).netloc + urlparse(district_domain).path
        if self.district_domain[len(self.district_domain) - 1] == '/':
            self.district_domain = self.district_domain[:-1]

        self.session = requests.Session()

        login_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_Login_Student.aspx?regenerateSessionId=True'.format(self.district_domain)).text, 'html.parser')

        form_data = helpers.parse_form(login_page.find(id='aspnetForm'))

        form_data['ctl00$MainContent$username'] = username
        form_data['ctl00$MainContent$password'] = password

        resp = self.session.post('https://{}/PXP2_Login_Student.aspx?regenerateSessionId=True'.format(
            self.district_domain), data=form_data)

        if resp.url != 'https://{}/Home_PXP2.aspx'.format(self.district_domain):
            raise ValueError('Incorrect Username or Password')

        home_page = BeautifulSoup(resp.text, 'html.parser')

        self.id_ = re.match(
            r'ID: ([0-9]+)', home_page.find(class_='student-id').text.strip()).group(1)
        self.name = home_page.find(class_='student-name').text

        self.school_name = home_page.find(class_='school').text
        self.school_phone = home_page.find(class_='phone').text

        self.picture_url = 'https://{}/{}'.format(self.district_domain,
                                                  home_page.find(alt='Student Photo')['src'])

        self.student_guid = re.match(r'Photos/[A-Z0-9]+/([A-Z0-9-]+)_Photo\.PNG',
                                     home_page.find(alt='Student Photo')['src']).group(1)

    def get_schedule(self):
        schedule_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_ClassSchedule.aspx?AGU=0'.format(self.district_domain)).text, 'html.parser')

        return self._parse_schedule_page(schedule_page)

    def _parse_schedule_page(self, schedule_page):
        script = schedule_page.find_all('script', {'type': 'text/javascript'})[-1]
        name, params = helpers.parse_data_grid(script.text)

        data = json.loads(self._get_data_grid(name, params, {
            'group': None,
            'requireTotalCount': True,
            'searchOperation': 'contains',
            'searchValue': None,
            'skip': 0,
            'sort': None,
            'take': 15
        }).text)['d']['Data']['data']

        return [
            models.Class(
                period=class_['Period'],
                name=class_['CourseTitle'],
                room=int(class_['RoomName']) if class_['RoomName'].isdigit() else class_['RoomName'],
                teacher=models.Teacher(
                    name=json.loads(class_['Teacher'])['teacherName'],
                    email=json.loads(class_['Teacher'])['email']
                ),
                class_id=class_['ID']
            ) for class_ in data
        ]

    def get_assignments(self, month=datetime.now().month, year=datetime.now().year):
        calendar_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_Calendar.aspx?AGU=0'.format(self.district_domain)).text, 'html.parser')

        if month is not datetime.now().month or year is not datetime.now().year:
            form_data = helpers.parse_form(calendar_page.find(id='aspnetForm'))
            form_data['LB'] = '{}/1/{}'.format(month, year)
            calendar_page = BeautifulSoup(self.session.post(
                'https://{}/PXP2_Calendar.aspx?AGU=0'.format(self.district_domain), data=form_data).text, 'html.parser')

        return self._parse_calendar_page(calendar_page)

    @staticmethod
    def _parse_calendar_page(calendar_page):
        return [
            models.Assignment(
                name=re.sub(r'- Score:.+', '', assignment.text[assignment.text.index(':') + 1:]).strip(),
                class_name=assignment.text[:assignment.text.index(':')].strip(),
                assignment_id=int(parse_qs(assignment['href'])['DGU'][0]),
                grading_period=parse_qs(assignment['href'])['GP'][0]
            ) for assignment in calendar_page.find_all('a', {'data-control': 'Gradebook_AssignmentDetails'})
        ]

    def get_student_info(self):
        student_info_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_MyAccount.aspx?AGU=0'.format(self.district_domain)).text, 'html.parser')

        return self._parse_student_info_page(student_info_page)

    @staticmethod
    def _parse_student_info_page(student_info_page):
        student_info_table = student_info_page.find('table', class_='info_tbl')

        tds = student_info_table.find_all('td')

        keys = [td.span.text for td in tds]

        for td in tds:
            td.span.clear()

        values = [td.get_text(separator='\n') for td in tds]

        return {
            k: v for (k, v) in zip(keys, values)
        }

    def get_school_info(self):
        school_info_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_SchoolInformation.aspx?AGU=0'.format(self.district_domain)).text, 'html.parser')

        return self._parse_school_info_page(school_info_page)

    @staticmethod
    def _parse_school_info_page(school_info_page):
        school_info_table = school_info_page.find('table')

        tds = school_info_table.find_all('td')

        keys = [td.span.text for td in tds]

        for td in tds:
            td.span.clear()

        values = [
            td.get_text(separator='\n') if len(td.find_all('span')) == 1 else models.Teacher(
                name=td.find_all('span')[1].text.strip(),
                email=helpers.parse_email(td.find_all('span')[1].find('a')['href'])
            )
            for td in tds
        ]

        return {
            k: v for (k, v) in zip(keys, values)
        }

    def get_image(self, fp):
        fp.write(self.session.get(self.picture_url).content)

    def _get_data_grid(self, name, params, load_options):
        return self.session.post('https://{}/service/PXP2Communication.asmx/DXDataGridRequest'.format(self.district_domain),
            json={
                'request': {
                    'agu': 0,
                    'dataRequestType': 'Load',
                    'dataSourceTypeName': name,
                    'gridParameters': json.dumps(params),
                    'loadOptions': load_options
                }
            }
        )
