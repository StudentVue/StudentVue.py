import requests
from bs4 import BeautifulSoup

from urllib.parse import urlparse

import json
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
            r'ID: ([0-9]+)', home_page.find(class_='student-id').text.strip()).group(1)
        self.name = home_page.find(class_='student-name').text

        self.school_name = home_page.find(class_='school').text
        self.school_phone = home_page.find(class_='phone').text

        self.picture_url = 'https://{}/{}'.format(self.districtdomain,
                                                  home_page.find(alt='Student Photo')['src'])

        self.student_guid = re.match(r'Photos/[A-Z0-9]+/([A-Z0-9-]+)_Photo\.PNG',
                                     home_page.find(alt='Student Photo')['src']).group(1)

    def getClasses(self):
        classes_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_Gradebook.aspx?AGU=0'.format(self.districtdomain)).text, 'html.parser')

        classes_table = classes_page.find('table')

        class_data = json.loads(
            re.search(r'PXP\.GBFocusData = ({.+});', classes_page.find_all('script')[1].text).group(1)
        )['GradingPeriods']

        grading_periods = [
            models.GradingPeriod(
                grading_period['GU'],
                grading_period['Name']
            ) for grading_period in class_data
        ]

        return [
            models.Class(
                int(class_.find('button').text[0]),
                class_.find('button').text[3:],
                re.match(r'Room: ([a-zA-z0-9]+)', class_.find(class_='teacher-room').text.strip()).group(1),
                models.Teacher(
                    class_.find('div', class_='teacher').text,
                    re.search(r'([a-zA-z0-9]+@[a-zA-z]+.[a-zA-z]+)', class_.find('span', class_='teacher').find('a')['href']).group(1)
                ),
                grading_periods,
                int(class_['data-guid']),
                int(class_data[0]['schoolID']),
                class_data[0]['OrgYearGU']
            ) for class_ in classes_table.find('tbody').find_all('tr', {'data-mark-gu': False})
        ]

    def getStudentInfo(self):
        student_info_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_Student.aspx?AGU=0'.format(self.districtdomain)).text, 'html.parser')

        student_info_table = student_info_page.find('table', class_='info_tbl')

        tds = student_info_table.find_all('td')

        keys = [td.span.text for td in tds]

        for td in tds:
            td.span.clear()

        values = [td.text for td in tds]

        return {
            k: v for (k, v) in zip(keys, values)
        }

    def getSchoolInfo(self):
        school_info_page = BeautifulSoup(self.session.get(
            'https://{}/PXP2_SchoolInformation.aspx?AGU=0'.format(self.districtdomain)).text, 'html.parser')

        school_info_table = school_info_page.find('table')

        tds = school_info_table.find_all('td')

        keys = [td.span.text for td in tds]

        for td in tds:
            td.span.clear()

        values = [
            td.text if len(td.find_all('span')) == 1 else models.Teacher(
                td.find_all('span')[1].text.strip(),
                re.search(r'([a-zA-z0-9]+@[a-zA-z]+.[a-zA-z]+)', td.find_all('span')[1].find('a')['href']).group(1)
            )
            for td in tds
        ]

        return {
            k: v for (k, v) in zip(keys, values)
        }

    """
        def getGrades(self, class_, grading_period):
        grading_info = self.session.post('https://{}/service/PXP2Communication.asmx/LoadControl'.format(self.districtdomain),
            data={
                "request":
                    {
                        "control": "Gradebook_ClassDetails",
                        "parameters": {
                            "schoolID": class_.school_id,
                            "classID": class_.class_id,
                            "gradePeriodGU": grading_period.period_guid,
                            "subjectID": -1,
                            "teacherID": -1,
                            "markPeriodGU": None,
                            "assignmentID": -1,
                            "standardIdentifier": None,
                            "viewName": None,
                            "studentGU": self.student_guid,
                            "AGU": "0",
                            "OrgYearGU": class_.org_id
                        }
                    }
            }
        )

        return grading_info"""
