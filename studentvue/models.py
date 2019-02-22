class Class:
    def __init__(self, period, name, room, teacher, grading_periods, class_id, school_id, org_id):
        self.period = period
        self.room = room
        self.name = name
        self.teacher = teacher

        self.grading_periods = grading_periods

        self.class_id = class_id
        self.school_id = school_id
        self.org_id = org_id

    def __repr__(self):
        return 'Period {period} {name} Taught by {teacher} in Room {room}'.format(
            **self.__dict__)

    def __str__(self):
        return self.__repr__()


class Teacher:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()


class GradingPeriod:
    def __init__(self, period_guid, name):
        self.period_guid = period_guid
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()
