from studentvue.ParamCache import ParamCache


class Control:
    name = 'None'
    params = []
    defaults = {}

    def __init__(self, params: dict):
        self.generated_params = {}

        param_stores = (params, ParamCache(), self.defaults)

        for param in self.params:
            for store in param_stores:
                if param in store:
                    self.generated_params[param] = store[param]
                    break
            else:
                raise ValueError('Required control parameter "' +
                                 param + '" not provided or stored in cache.')


class Gradebook_SchoolClasses_Control(Control):
    name = 'Gradebook_SchoolClasses'
    params = ['AGU', 'gradePeriodGU', 'GradingPeriodGroup', 'OrgYearGU', 'schoolID']
    defaults = {'AGU': 0, 'GradingPeriodGroup': 'Regular'}
