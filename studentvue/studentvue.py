import requests
from bs4 import BeautifulSoup

from urllib.parse import urlparse

from datetime import datetime
import json
import re

import studentvue.helpers as helpers
from studentvue.parser import StudentVueParser


class StudentVue:
    """The StudentVue scraper object."""
    def __init__(self, username, password, district_domain, parser=StudentVueParser):
        """
        :param username: your StudentVue account's username
        :type username: str
        :param password: your StudentVue account's password
        :type password: str
        :param district_domain: your school district's StudentVue domain
        :type district_domain: str
        """
        self.parser = parser

        self.district_domain = urlparse(district_domain).netloc + urlparse(district_domain).path
        if self.district_domain[len(self.district_domain) - 1] == '/':
            self.district_domain = self.district_domain[:-1]

        self.session = requests.Session()

        login_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_Login_Student.aspx?regenerateSessionId=True'.format(self.district_domain)).text,
                                   'html.parser')

        login_form_data = helpers.parse_form(login_page.find(id='aspnetForm'))

        login_form_data['ctl00$MainContent$username'] = username
        login_form_data['ctl00$MainContent$password'] = password

        resp = self.session.post('https://{}/PXP2_Login_Student.aspx?regenerateSessionId=True'.format(
            self.district_domain), data=login_form_data)

        if resp.url != 'https://{}/Home_PXP2.aspx'.format(self.district_domain):
            raise ValueError('Incorrect Username or Password')

        home_page = BeautifulSoup(resp.text, 'html.parser')
        home_page_data = self.parser.parse_home_page(home_page)

        self.id_ = home_page_data['id_']
        self.name = home_page_data['name']

        self.school_name = home_page_data['school_name']
        self.school_phone = home_page_data['school_phone']

        self.picture_url = 'https://{}/{}'.format(self.district_domain, home_page_data['picture_src'])
        self.student_guid = home_page_data['student_guid']

    def get_schedule(self, semester=None):
        """
        :param semester: (optional) if provided, it will get the schedule for that semester instead of the default one
        :type semester: int
        :return: a list of the classes you're taking
        :rtype: list of studentvue.models.Class
        """
        if semester is not None:
            semester_parameter = '&VDT=' + str(semester)
        else:
            semester_parameter = ''

        schedule_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_ClassSchedule.aspx?AGU=0'.format(self.district_domain) +
            semester_parameter).text, 'html.parser')

        script = schedule_page.find_all('script', {'type': 'text/javascript'})[-1]
        try:
            name, params = helpers.parse_data_grid(script.text)
        except AttributeError:
            return []

        schedule_data = self._get_data_grid(name, params, {
            'group': None,
            'requireTotalCount': True,
            'searchOperation': 'contains',
            'searchValue': None,
            'skip': 0,
            'sort': None,
            'take': 15
        })

        return self.parser.parse_schedule_data(schedule_data)

    def get_assignments(self, month=datetime.now().month, year=datetime.now().year):
        """
        :param month: the month to get assignments from, defaults to the current month
        :type month: int
        :param year: the year to get assignments from, defaults to the current year
        :type year: int
        :return: a list of the assignments due in the specified month
        :rtype: list of studentvue.model.Assignment
        """
        calendar_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_Calendar.aspx?AGU=0'.format(self.district_domain)).text, 'html.parser')

        if month is not datetime.now().month or year is not datetime.now().year:
            calender_form_data = helpers.parse_form(calendar_page.find(id='aspnetForm'))
            calender_form_data['LB'] = '{}/1/{}'.format(month, year)
            calendar_page = BeautifulSoup(self.session.post(
                'https://{}/PXP2_Calendar.aspx?AGU=0'.format(self.district_domain), data=calender_form_data).text, 'html.parser')

        return self.parser.parse_calendar_page(calendar_page)

    def get_student_info(self):
        """
        :return: miscellaneous student information
        :rtype: dict of (str, str)
        """
        student_info_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_MyAccount.aspx?AGU=0'.format(self.district_domain)).text, 'html.parser')

        return self.parser.parse_student_info_page(student_info_page)

    def get_school_info(self):
        """
        :return: miscellaneous school information
        :rtype: dict of (str, str)
        """
        school_info_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_SchoolInformation.aspx?AGU=0'.format(self.district_domain)).text, 'html.parser')

        return self.parser.parse_school_info_page(school_info_page)

    def get_class_info(self, class_):
        """
        :param class_: the class to get info for
        :type class_: studentvue.models.Class
        :return: your current grades and assignments in the specified class
        :rtype: dict containing `grade`, `mark`, and `assignments` keys
        """
        grade_book_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_Gradebook.aspx?AGU=0'.format(self.district_domain)).text, 'html.parser')

        button = grade_book_page.find('button',
                                      text='{period}: {name}'.format(**class_.__dict__),
                                      class_='course-title')

        if button is None:
            return None

        focus_data = json.loads(button['data-focus'])

        grade_book_class_page = self._get_load_control(
            focus_data['LoadParams']['ControlName'],
            focus_data['FocusArgs']
        )

        return self.parser.parse_grade_book_class_page(grade_book_class_page, class_.name)

    def get_course_history(self):
        """
        :return: your full course history, including semester grades and number of credits earned per class.
        :rtype: dict of grade year paired with a list of semesters, each semester being a list of type studentvue.models.Course
        """
        course_history_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_CourseHistory.aspx?AGU=0'.format(self.district_domain)).text, 'html.parser')
        return self.parser.parse_course_history_page(course_history_page)

    def get_grade_book(self):
        """
        :return: your mark and score in all your graded classes
        :rtype: dict of class name paired with a dict containing `mark` and `score` keys
        """
        grade_book_page = BeautifulSoup(self.session.get('https://{}/PXP2_Gradebook.aspx?AGU=0'.format(self.district_domain)).text, 'html.parser')
        return self.parser.parse_grade_book_page(grade_book_page)

    def get_image(self, fp):
        """
        :param fp: file-like object to write to
        :return: your school photo
        :rtype fp: PyFileObject
        """
        fp.write(self.session.get(self.picture_url).content)

    def _get_data_grid(self, name, params, load_options):
        data_grid = json.loads(self.session.post('https://{}/service/PXP2Communication.asmx/DXDataGridRequest'.format(self.district_domain),
            json={
                'request': {
                    'agu': 0,
                    'dataRequestType': 'Load',
                    'dataSourceTypeName': name,
                    'gridParameters': json.dumps(params),
                    'loadOptions': load_options
                }
            }
        ).text)

        data = data_grid['d']['Data']['data']

        return data

    def _get_load_control(self, control, params):
        load_control = json.loads(self.session.post('https://{}/service/PXP2Communication.asmx/LoadControl'.format(self.district_domain),
            json={
                'request': {
                    'control': control,
                    'parameters': params
                }
            }
        ).text)

        soup = BeautifulSoup(load_control['d']['Data']['html'], 'html.parser')

        return soup
