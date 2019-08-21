class Class:
    def __init__(self, period, name, room, teacher, grade, grading_periods, class_id, school_id, org_id):
        self.period = period
        self.room = room
        self.name = name
        self.teacher = teacher
        self.grade = grade

        self.grading_periods = grading_periods

        self.class_id = class_id
        self.school_id = school_id
        self.org_id = org_id

    def __repr__(self):
        return 'Period {period} {name} Taught by {teacher} in Room {room}'.format(
            **self.__dict__)


class Teacher:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return self.name


class Assignment:
    def __init__(self, name, class_, assignment_id, grading_period):
        self.name = name
        self.class_ = class_
        self.assignment_id = assignment_id
        self.grading_period = grading_period

    def __repr__(self):
        return self.name


class GradingPeriod:
    def __init__(self, period_id, name):
        self.period_id = period_id
        self.name = name

    def __repr__(self):
        return self.name
