class Class(dict):
    def __init__(self, period, name, room, teacher, class_id):
        self.period = period
        self.room = room
        self.name = name
        self.teacher = teacher

        self.class_id = class_id

        super().__init__(**self._asdict())

    def __repr__(self):
        return 'Period {period} {name} Taught by {teacher} in Room {room}'.format(
            **self.__dict__)

    def _asdict(self):
        return self.__dict__


class Teacher(dict):
    def __init__(self, name, email):
        self.name = name
        self.email = email

        super().__init__(**self._asdict())

    def __repr__(self):
        return self.name

    def _asdict(self):
        return self.__dict__


class Assignment(dict):
    def __init__(self, name, class_name, date, assignment_id, grading_period, org_year_id):
        self.name = name
        self.class_name = class_name
        self.date = date
        self.assignment_id = assignment_id
        self.grading_period = grading_period
        self.org_year_id = org_year_id

        super().__init__(**self._asdict())

    def __repr__(self):
        return self.name

    def _asdict(self):
        __dict__ = dict(self.__dict__)
        __dict__['date'] = __dict__['date'].isoformat()
        return __dict__


class GradedAssignment(Assignment):
    def __init__(self, name, class_name, date, assignment_id, grading_period, org_year_id, score, max_score):
        super().__init__(name, class_name, date, assignment_id, grading_period, org_year_id)
        self.score = score
        self.max_score = max_score

        dict.__init__(self, **self._asdict())


class Course(dict):
    def __init__(self, name, mark, credits_attempted, credits_completed):
        self.name = name
        self.mark = mark
        self.credits_attempted = credits_attempted
        self.credits_completed = credits_completed

        super().__init__(**self._asdict())

    @property
    def is_ap(self):
        return 'AP' in self.name

    def __repr__(self):
        return self.name

    def _asdict(self):
        return self.__dict__


class MarkingPeriod(dict):
    def __init__(self, name, grade_book_control_params):
        self.name = name
        self.grade_book_control_params = grade_book_control_params
        self.parent = None

        super().__init__(**self._asdict())

    def _asdict(self):
        __dict__ = dict(self.__dict__)
        __dict__.pop('grade_book_control_params')
        __dict__.pop('parent')
        return __dict__


class GradedMarkingPeriod(MarkingPeriod):
    def __init__(self, name, mark, score, grade_book_control_params):
        super().__init__(name, grade_book_control_params)
        self.mark = mark
        self.score = score

        dict.__init__(self, **self._asdict())


class GradeBookEntry(dict):
    def __init__(self, name, marking_periods):
        self.name = name
        self.marking_periods = marking_periods

        for marking_period in self.marking_periods:
            marking_period.parent = self

        super().__init__(**self._asdict())

    def _asdict(self):
        __dict__ = dict(self.__dict__)
        __dict__['marking_periods'] = [marking_period._asdict() for marking_period in __dict__['marking_periods']]
        return __dict__
