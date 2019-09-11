import requests
from bs4 import BeautifulSoup

from urllib.parse import urlparse, parse_qs

from datetime import datetime
import json
import re

import studentvue.models as models
import studentvue.helpers as helpers


class StudentVue:
    """The StudentVue scraper object."""
    def __init__(self, username, password, district_domain):
        """
        :param username: your StudentVue account's username
        :type username: str
        :param password: your StudentVue account's password
        :type password: str
        :param district_domain: your school district's StudentVue domain
        :type district_domain: str
        """
        self.district_domain = urlparse(district_domain).netloc + urlparse(district_domain).path
        if self.district_domain[len(self.district_domain) - 1] == '/':
            self.district_domain = self.district_domain[:-1]

        self.session = requests.Session()

        login_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_Login_Student.aspx?regenerateSessionId=True'.format(self.district_domain)).text,
                                   'html.parser')

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

        picture_src = home_page.find(alt='Student Photo')['src']

        self.picture_url = 'https://{}/{}'.format(self.district_domain, picture_src)

        self.student_guid = re.match(r'Photos/[A-Z0-9]+/([A-Z0-9-]+)_Photo\.PNG', picture_src).group(1) \
            if picture_src != 'Images/PXP/NoPhoto.png' else None

    def get_schedule(self, semester=None):
        """
        :param semester: (optional) if provided, it will get the schedule for that semester instead of the default one
        :type semester: int
        :return: a list of the classes you're taking
        :rtype: list of studentvue.models.Class
        """
        if semester is not None:
            extra = '&VDT=' + str(semester)
        else:
            extra = ''

        schedule_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_ClassSchedule.aspx?AGU=0'.format(self.district_domain) + extra).text, 'html.parser')

        script = schedule_page.find_all('script', {'type': 'text/javascript'})[-1]
        try:
            name, params = helpers.parse_data_grid(script.text)
        except AttributeError:
            return []

        schedule_data = json.loads(self._get_data_grid(name, params, {
            'group': None,
            'requireTotalCount': True,
            'searchOperation': 'contains',
            'searchValue': None,
            'skip': 0,
            'sort': None,
            'take': 15
        }).text)['d']['Data']['data']

        return self._parse_schedule_data(schedule_data)

    @staticmethod
    def _parse_schedule_data(schedule_data):
        classes = []

        for class_ in schedule_data:
            teacher = json.loads(class_['Teacher'])

            classes.append(models.Class(
                period=class_['Period'],
                name=class_['CourseTitle'],
                room=int(class_['RoomName']) if class_['RoomName'].isdigit() else class_['RoomName'],
                teacher=models.Teacher(
                    name=teacher['teacherName'],
                    email=teacher['email']
                ),
                class_id=class_['ID']
            ))

        return classes

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
            form_data = helpers.parse_form(calendar_page.find(id='aspnetForm'))
            form_data['LB'] = '{}/1/{}'.format(month, year)
            calendar_page = BeautifulSoup(self.session.post(
                'https://{}/PXP2_Calendar.aspx?AGU=0'.format(self.district_domain), data=form_data).text, 'html.parser')

        return self._parse_calendar_page(calendar_page)

    @staticmethod
    def _parse_calendar_page(calendar_page):
        assignments = []

        for assignment in calendar_page.find_all('a', {'data-control': 'Gradebook_AssignmentDetails'}):
            qs = parse_qs(assignment['href'])

            assignments.append(models.Assignment(
                name=re.sub(r'- Score:.+', '', assignment.text[assignment.text.index(':') + 1:]).strip(),
                class_name=assignment.text[:assignment.text.index(':')].strip(),
                date=datetime.strptime(assignment.parent.parent.find('span', class_='datePick')['onclick'],
                                       'ChangeView(\'2\', \'%m/%d/%Y\')'),
                assignment_id=int(qs['DGU'][0]),
                grading_period=qs['GP'][0],
                org_year_id=qs['SSY'][0]
            ))

        return assignments

    def get_student_info(self):
        """
        :return: miscellaneous student information
        :rtype: dict of (str, str)
        """
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
        """
        :return: miscellaneous school information
        :rtype: dict of (str, str)
        """
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

        grade_book_class_page = BeautifulSoup(json.loads(self._get_load_control(
            focus_data['LoadParams']['ControlName'],
            focus_data['FocusArgs']
        ).text)['d']['Data']['html'], 'html.parser')

        return self._parse_grade_book_class_page(grade_book_class_page, class_.name)

    def get_course_history(self):
        """
        :return: Your full course history, including semester grades and number of credits earned per class.
        :rtype: dict of a key of type studentvue.models.Course for each grade
        """
        course_history_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_CourseHistory.aspx?AGU=0'.format(self.district_domain)).text, 'html.parser')
        course_data = course_history_page.find('div', class_='chs-course-history').div
        yearly_tables = course_data.find_all('table')
        yearly_labels = course_data.find_all('h2')
        course_history = {}
        for i in range(len(yearly_tables)):
            current_table = yearly_tables[i]
            current_courses = []
            rows = current_table.tbody.find_all('tr')
            del rows[0]
            for x in rows:
                course = list(filter(lambda index: (index != '\n'), x.strings))
                current_courses.append(models.Course(course[0],course[1],course[2],course[3],course[0].find("AP ") != -1))
            course_history[yearly_labels[i].contents[2].strip()] = current_courses
        return course_history

    @staticmethod
    def _parse_grade_book_class_page(grade_book_page, class_name):
        assignments = []

        for assignment in json.loads(
                re.sub(r'PXP\.(?:(?:DataGridTemplates)|(?:DevExpress))\.([A-Za-z]+)',
                       lambda match: '"{}"'.format(match.group(1)), re.search(
                        r'PXP\.DevExpress\.ExtendGridConfiguration\(\W+({.+})\W+\)',
                        grade_book_page.find_all('script', {'type': 'text/javascript'})[-1].text).group(1)
                       )
        )['dataSource']:
            focus_args = json.loads(
                    re.search(r'data-focus=({.+})', json.loads(
                        assignment['GBAssignment'])['hrefAttributes']).group(1)
            )['FocusArgs']

            assignments.append(models.GradedAssignment(
                name=json.loads(assignment['GBAssignment'])['value'],
                class_name=class_name,
                date=datetime.strptime(assignment['Date'], '%m/%d/%Y'),
                assignment_id=int(assignment['gradeBookId']),
                grading_period=focus_args['gradePeriodGU'],
                org_year_id=focus_args['OrgYearGU'],
                score=None if 'Points Possible' in assignment['GBPoints']
                else float(assignment['GBPoints'].split('/')[0]),
                max_score=float(assignment['GBPoints'].replace(' Points Possible', ''))
                if 'Points Possible' in assignment['GBPoints']
                else float(assignment['GBPoints'].split('/')[1])
            ))

        return {
            'mark': grade_book_page.find('div', class_='mark').text,
            'score': float(grade_book_page.find('div', class_='score').text[:-1]),
            'assignments': assignments
        }

    def get_image(self, fp):
        """
        :param fp: file-like object to write to
        :type fp: PyFileObject
        """
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

    def _get_load_control(self, control, params):
        return self.session.post('https://{}/service/PXP2Communication.asmx/LoadControl'.format(self.district_domain),
            json={
                'request': {
                    'control': control,
                    'parameters': params
                }
            }
        )
