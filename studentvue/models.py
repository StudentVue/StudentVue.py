class Class:
    def __init__(self, period, name, room, teacher, grade):
        self.period = period
        self.room = room
        self.name = name
        self.teacher = teacher
        self.grade = grade

    def __repr__(self):
        return 'Period {period} {name} Taught by {teacher} in Room {room} with a Grade of {grade}'.format(**self.__dict__)

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
