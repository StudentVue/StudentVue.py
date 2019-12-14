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

        return dict(
            id_=id_,
            name=name,
            school_name=school_name,
            school_phone=school_phone,
            picture_src=picture_src,
            student_guid=student_guid
        )

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
            query_string = parse_qs(assignment['href'])

            assignments.append(models.Assignment(
                name=re.sub(r'- Score:.+', '', assignment.text[assignment.text.index(':') + 1:]).strip(),
                class_name=assignment.text[:assignment.text.index(':')].strip(),
                date=datetime.strptime(assignment.parent.parent.find('span', class_='datePick')['onclick'],
                                       'ChangeView(\'2\', \'%m/%d/%Y\')'),
                assignment_id=int(query_string['DGU'][0]),
                grading_period=query_string['GP'][0],
                org_year_id=query_string['SSY'][0]
            ))

        return assignments

    @staticmethod
    def parse_student_info_page(student_info_page):
        student_info_table = student_info_page.find('table', class_='info_tbl')

        cells = student_info_table.find_all('td')

        keys = [cell.span.text for cell in cells]

        for cell in cells:
            cell.span.clear()

        values = [cell.get_text(separator='\n') for cell in cells]

        return {
            k: v for (k, v) in zip(keys, values)
        }

    @staticmethod
    def parse_school_info_page(school_info_page):
        school_info_table = school_info_page.find('table')

        cells = school_info_table.find_all('td')

        keys = [cell.span.text for cell in cells]

        for cell in cells:
            cell.span.clear()

        values = [
            cell.get_text(separator='\n') if len(cell.find_all('span')) == 1 else models.Teacher(
                name=cell.find_all('span')[1].text.strip(),
                email=helpers.parse_email(cell.find_all('span')[1].find('a')['href'])
            )
            for cell in cells
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

        return dict(
            mark=grade_book_page.find('div', class_='mark').text,
            score=float(grade_book_page.find('div', class_='score').text[:-1]),
            assignments=assignments
        )

    @staticmethod
    def parse_course_history_page(course_history_page):
        course_history_div = course_history_page.find('div', class_='chs-course-history').div
        yearly_tables = course_history_div.find_all('table')
        yearly_labels = course_history_div.find_all('h2')
        course_history = {}
        for (current_table, year_label) in zip(yearly_tables, yearly_labels):
            semesters = current_table.find_all('tbody')
            semesters_courses = []
            for semester in semesters:
                rows = semester.find_all('tr')
                del rows[0]
                current_courses = []
                for row in rows:
                    course_data = list(filter(lambda string: (string != '\n'), row.strings))
                    current_courses.append(models.Course(
                        name=course_data[0],
                        mark=course_data[1],
                        credits_attempted=float(course_data[2]),
                        credits_completed=float(course_data[3])
                    ))
                semesters_courses.append(current_courses)
            course_history[year_label.contents[2].strip()] = semesters_courses
        return course_history

    @staticmethod
    def parse_grade_book_page(grade_book_page):
        grade_book = []

        tbody = grade_book_page.find('tbody')
        for course_button in tbody.find_all('button', class_='btn btn-link course-title'):
            marking_periods = []
            course_name = re.match(r'[0-9]+: (.+)', course_button.text).group(1)
            data_guid = course_button.parent.parent['data-guid']
            for mark_tr in tbody.find_all('tr', {'data-guid': data_guid, 'data-mark-gu': True}):
                mark_period_button = mark_tr.find('button', class_='course-markperiod')
                mark = mark_tr.find('span', class_='mark').text
                score = mark_tr.find('span', class_='score').text
                marking_periods.append(models.GradedMarkingPeriod(
                    name=mark_period_button.text,
                    mark=mark,
                    score=score,
                    grade_book_control_params=json.loads(mark_period_button['data-focus'])['FocusArgs']
                ))

            grade_book.append(models.GradeBookEntry(
                name=course_name,
                marking_periods=marking_periods
            ))

        return grade_book
