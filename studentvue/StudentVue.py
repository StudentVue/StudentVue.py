from requests_cache import CachedSession
from requests_cache.backends import BaseCache
from bs4 import BeautifulSoup

from urllib.parse import urlparse

from datetime import datetime
import re
import json

from studentvue.StudentVueParser import StudentVueParser
import studentvue.helpers as helpers
import studentvue.models as models

import typing

URLS = {
    'LOGIN': 'https://{}/PXP2_Login_Student.aspx?regenerateSessionId=True',
    'HOME': 'https://{}/Home_PXP2.aspx',
    'SCHEDULE': 'https://{}/PXP2_ClassSchedule.aspx?AGU=0',
    'CALENDAR': 'https://{}/PXP2_Calendar.aspx?AGU=0',
    'STUDENT_INFO': 'https://{}/PXP2_MyAccount.aspx?AGU=0',
    'SCHOOL_INFO': 'https://{}/PXP2_SchoolInformation.aspx?AGU=0',
    'COURSE_HISTORY': 'https://{}/PXP2_CourseHistory.aspx?AGU=0',
    'GRADE_BOOK': 'https://{}/PXP2_Gradebook.aspx?AGU=0',
    'DATA_GRID': 'https://{}/service/PXP2Communication.asmx/DXDataGridRequest',
    'LOAD_CONTROL': 'https://{}/service/PXP2Communication.asmx/LoadControl'
}


class StudentVue:
    """The StudentVue scraper object."""

    def __init__(self,
                 username: str,
                 password: str,
                 district_domain: str,
                 parser: typing.Type[StudentVueParser] = StudentVueParser,
                 cache_backend: typing.Union[typing.Type[BaseCache], str] = 'memory'
                 ):
        """
        :param username: your StudentVue account's username
        :type username: str
        :param password: your StudentVue account's password
        :type password: str
        :param district_domain: your school district's StudentVue domain
        :type district_domain: str
        :param parser: HTML/JSON parser that extracts relevant data
        :type parser: studentvue.StudentVueParser.StudentVueParser
        :param cache_backend: requests-cache backend
        :type cache_backend: requests_cache.backends.BaseCache
        """

        self.parser = parser

        self.district_domain = urlparse(district_domain).netloc + urlparse(district_domain).path
        if self.district_domain[len(self.district_domain) - 1] == '/':
            self.district_domain = self.district_domain[:-1]

        self.session = CachedSession(
            cache_name=username,
            backend=cache_backend,
            expire_after=15 * 60,
            allowable_methods=('GET', 'POST')
        )

        login_page = BeautifulSoup(self.session.get(URLS['LOGIN'].format(self.district_domain)).text, 'html.parser')

        try:
            login_form_data = helpers.parse_form(login_page.find(id='aspnetForm'))
        except AttributeError:
            raise Exception("""
This library getting an AttributeError when trying to log in, which might mean that your school is on an older version of StudentVue.
Try uninstalling this library (pip uninstall studentvue) and installing studentvue-old (pip uninstall studentvue-old).
studentvue-old is not maintained and has a different API, but there is some minimal documentation: https://github.com/kajchang/StudentVue/tree/old-version.
            """)

        login_form_data['ctl00$MainContent$username'] = username
        login_form_data['ctl00$MainContent$password'] = password

        resp = self.session.post(URLS['LOGIN'].format(self.district_domain), data=login_form_data)

        if resp.url != URLS['HOME'].format(self.district_domain):
            raise ValueError('Incorrect Username or Password')

        home_page = BeautifulSoup(resp.text, 'html.parser')
        home_page_data = self.parser.parse_home_page(home_page)

        self.id_ = home_page_data['id_']
        self.name = home_page_data['name']

        self.school_name = home_page_data['school_name']
        self.school_phone = home_page_data['school_phone']

        self.picture_url = 'https://{}/{}'.format(self.district_domain, home_page_data['picture_src'])
        self.student_guid = home_page_data['student_guid']

    def get_schedule(self, semester: int = None) -> typing.List[models.Class]:
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

        schedule_page = BeautifulSoup(self.session.get(URLS['SCHEDULE'].format(self.district_domain) +
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

        return self.parser.parse_schedule_data(
            typing.cast(typing.List[typing.Dict[str, str]], schedule_data)
        )

    def get_assignments(self,
                        month: int = datetime.now().month,
                        year: int = datetime.now().year) -> typing.List[models.Assignment]:
        """
        :param month: the month to get assignments from, defaults to the current month
        :type month: int
        :param year: the year to get assignments from, defaults to the current year
        :type year: int
        :return: a list of the assignments due in the specified month
        :rtype: list of studentvue.model.Assignment
        """
        calendar_page = BeautifulSoup(self.session.get(URLS['CALENDAR'].format(self.district_domain)).text,
                                      'html.parser')

        if month is not datetime.now().month or year is not datetime.now().year:
            calendar_form_data = helpers.parse_form(calendar_page.find(id='aspnetForm'))
            calendar_form_data['LB'] = '{}/1/{}'.format(month, year)
            calendar_page = BeautifulSoup(self.session.post(URLS['CALENDAR'].format(self.district_domain),
                                                            data=calendar_form_data).text,
                                          'html.parser')

        return self.parser.parse_calendar_page(calendar_page)

    def get_student_info(self) -> typing.Dict[str, str]:
        """
        :return: miscellaneous student information
        :rtype: dict of (str, str)
        """
        student_info_page = BeautifulSoup(self.session.get(URLS['STUDENT_INFO'].format(self.district_domain)).text,
                                          'html.parser')

        return self.parser.parse_student_info_page(student_info_page)

    def get_school_info(self) -> typing.Dict[str, str]:
        """
        :return: miscellaneous school information
        :rtype: dict of (str, str)
        """
        school_info_page = BeautifulSoup(self.session.get(URLS['SCHOOL_INFO'].format(self.district_domain)).text,
                                         'html.parser')

        return self.parser.parse_school_info_page(school_info_page)

    """
    def get_marking_period_info(self, marking_period):
        """"""
        :param marking_period: the class to get info for
        :type marking_period: studentvue.models.MarkingPeriod
        :return: your current grades and assignments in the specified class
        :rtype: dict containing `grade`, `mark`, and `assignments` keys
        """"""
        grade_book_class_page = self._get_load_control(
            'Gradebook_ClassDetails',
            marking_period.grade_book_control_params
        )

        return self.parser.parse_grade_book_class_page(grade_book_class_page, marking_period.for_)
    """

    def get_course_history(self) -> typing.Dict[str, typing.List[typing.List[models.Course]]]:
        """
        :return: your full course history, including semester grades and number of credits earned per class.
        :rtype: dict of grade year paired with a list of semesters, each semester being a list of type studentvue.models.Course
        """
        course_history_page = BeautifulSoup(self.session.get(URLS['COURSE_HISTORY'].format(self.district_domain)).text,
                                            'html.parser')
        return self.parser.parse_course_history_page(course_history_page)

    def get_grading_periods(self) -> typing.List[str]:
        """
        :return: your school's grading periods
        :rtype: list of grading period names
        """
        grade_book_page = BeautifulSoup(self.session.get(URLS['GRADE_BOOK'].format(self.district_domain)).text,
                                        'html.parser')

        return self.parser.parse_grade_book_page_for_grading_periods(grade_book_page)

    def get_grade_book(self, grading_period: str = None) -> typing.Dict[str, dict]:
        """
        :return: your mark and score in all your graded classes
        :rtype: dict of class names paired with a list of dicts of
                `score` - grade as a percentage
                `mark` - letter grade
                `marking_period` - marking period
                `grading_period` - grading period
        """
        grade_book_page = BeautifulSoup(self.session.get(URLS['GRADE_BOOK'].format(self.district_domain)).text,
                                        'html.parser')

        if grading_period is not None:
            dropdown_menu = grade_book_page.find('ul', class_='dropdown-menu')
            grading_period_link = dropdown_menu.find('a', text=re.compile(r'\s+' + grading_period + r'\s+'))

            update_panel = grade_book_page.find('div', class_='update-panel')

            grade_book_page = self._load_control('Gradebook_SchoolClasses', {
                'AGU': 0,
                'gradePeriodGU': grading_period_link['data-period-id'],
                'GradingPeriodGroup': 'Regular',
                'OrgYearGU': update_panel['data-orgyear-id'],
                'schoolID': update_panel['data-school-id']
            })

        return self.parser.parse_grade_book_page_for_grades(grade_book_page)

    def get_image(self, fp: typing.BinaryIO) -> None:
        """
        :param fp: file-like object to write to
        :return: your school photo
        :rtype fp: PyFileObject
        """
        fp.write(self.session.get(self.picture_url).content)

    def _get_data_grid(self, name: str, params: dict, load_options: dict) -> object:
        data_grid = json.loads(self.session.post(
            URLS['DATA_GRID'].format(self.district_domain),
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

    def _load_control(self, control_name: str, params: dict) -> BeautifulSoup:
        control = json.loads(self.session.post(
            URLS['LOAD_CONTROL'].format(self.district_domain),
            json={
                'request': {
                    'control': control_name,
                    'parameters': params
                }
            }
        ).text)

        soup = BeautifulSoup(control['d']['Data']['html'], 'html.parser')

        return soup