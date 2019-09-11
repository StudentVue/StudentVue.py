from unittest import TestCase
import os

from studentvue import StudentVue
import studentvue.models as models

class TestCourseHistory(TestCase):
    """A test case for the StudentVue.get_course_history function."""
    def test_valid_courses(self):
        if os.environ.get('TEST_USERNAME') == None:
            print('Skipping test, no test username or password used...')
            return
        sv = StudentVue(os.environ.get('TEST_USERNAME'), os.environ.get('TEST_PASSWORD'), 'portal.sfusd.edu')
        ch = sv.get_course_history()
        key = iter(ch).__next__()
        self.assertIsInstance(ch[key][0], models.Course)
