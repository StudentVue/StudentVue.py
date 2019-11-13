from urllib.parse import parse_qs

from datetime import datetime
import json
import re

import studentvue.models as models
import studentvue.helpers as helpers


class StudentVueParser:
    @staticmethod
    def parse_home_page(home_page):
        id_ = re.match(
            r'ID: ([0-9]+)', home_page.find(class_='student-id').text.strip()).group(1)
        name = home_page.find(class_='student-name').text

        school_name = home_page.find(class_='school').text
        school_phone = home_page.find(class_='phone').text

        picture_src = home_page.find(alt='Student Photo')['src']

        student_guid = re.match(r'Photos/[A-Z0-9]+/([A-Z0-9-]+)_Photo\.PNG', picture_src).group(1) \
            if picture_src != 'Images/PXP/NoPhoto.png' else None

        return {
            'id_': id_,
            'name': name,
            'school_name': school_name,
            'school_phone': school_phone,
            'picture_src': picture_src,
            'student_guid': student_guid
        }

    @staticmethod
    def parse_schedule_data(schedule_data):
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

    @staticmethod
    def parse_calendar_page(calendar_page):
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

    @staticmethod
    def parse_student_info_page(student_info_page):
        student_info_table = student_info_page.find('table', class_='info_tbl')

        tds = student_info_table.find_all('td')

        keys = [td.span.text for td in tds]

        for td in tds:
            td.span.clear()

        values = [td.get_text(separator='\n') for td in tds]

        return {
            k: v for (k, v) in zip(keys, values)
        }

    @staticmethod
    def parse_school_info_page(school_info_page):
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

    @staticmethod
    def parse_grade_book_class_page(grade_book_page, class_name):
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

    @staticmethod
    def parse_course_history_page(course_history_page):
        course_data = course_history_page.find('div', class_='chs-course-history').div
        yearly_tables = course_data.find_all('table')
        yearly_labels = course_data.find_all('h2')
        course_history = {}
        for i in range(len(yearly_tables)):
            current_table = yearly_tables[i]
            semesters = current_table.find_all('tbody')
            semesters_courses = []
            for semester in semesters:
                courses = semester.find_all('tr')
                del courses[0]
                current_courses = []
                for x in courses:
                    course = list(filter(lambda index: (index != '\n'), x.strings))
                    current_courses.append(models.Course(
                        name=course[0],
                        mark=course[1],
                        credits_attempted=float(course[2]),
                        credits_completed=float(course[3]),
                    ))
                semesters_courses.append(current_courses)
            course_history[yearly_labels[i].contents[2].strip()] = semesters_courses
        return course_history

    @staticmethod
    def parse_grade_book_page(grade_book_page):
        tbody = grade_book_page.find('tbody')
        titles = [title.text[3::] for title in tbody.find_all('button', {'class': 'btn btn-link course-title'})]
        marks = [mark.text for mark in tbody.find_all('span', {'class': 'mark'})]
        scores = [score.text for score in tbody.find_all('span', {'class': 'score'})]
        return {t: {'mark': m, 'score': s} for (t, m, s) in zip(titles, marks, scores)}
