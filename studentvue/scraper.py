from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from robobrowser import RoboBrowser


class StudentVue:
    def __init__(self, username, password, districtdomain, driverpath='/usr/local/bin/chromedriver'):
        """The StudentVue scraper object.
        Args:
            username (str): The username of the student portal account
            password (str): The password of the student portal account
            districtdomain (str): The domain name of your student portal
            driverpath (str, optional): Custom path to Chrome driver
        """
        self.username = username
        self.password = password
        self.districtdomain = districtdomain
        if not self.districtdomain.startswith('https://'):
            self.districtdomain = 'https://' + self.districtdomain
        if not self.districtdomain.endswith('/'):
            self.districtdomain += '/'
        self.districtdomain = self.districtdomain + '{}'
        self.driverpath = driverpath
        self.login()

    def login(self):
        """Logins into the student portal account
        Returns:
            A signed in browser object
        Raises:
            Exception: If the password and username password is invalid
        """
        options = Options()
        options.set_headless(headless=True)
        browser = webdriver.Chrome(
            chrome_options=options,
            executable_path=self.driverpath)
        browser.get(self.districtdomain.format(
            'Login_Student_PXP.aspx?regenerateSessionId=True'))
        browser.find_element_by_id("username").send_keys(self.username)
        browser.find_element_by_id("password").send_keys(self.password)
        browser.find_element_by_id("Submit1").click()
        if not browser.current_url.endswith('Home_PXP.aspx'):
            browser.close()
            raise Exception('Password and Username Combination are Invalid')
        return browser

    def getSchedule(self):
        """Gets the student's schedule
        Returns:
            A list containing dictionaries with basic information for each class
        """
        browser = self.login()
        browser.get(self.districtdomain.format('PXP_ClassSchedule.aspx?AGU=0'))

        table = browser.find_element_by_class_name('info_tbl')
        rows = table.find_element_by_tag_name('tbody')

        raw_data = [[data.text for data in row.find_elements_by_tag_name(
            'td')] for row in rows.find_elements_by_tag_name('tr')]

        class_data = []

        for classes in raw_data[1:]:
            this_class_data = {}
            for attribute in raw_data[0]:
                this_class_data[attribute] = classes[raw_data[0].index(
                    attribute)]
            class_data.append(this_class_data)

        browser.close()
        return class_data

    def getStudentContactInfo(self):
        """Gets the student's contact information
        Returns:
            A dictionary with contact information on the student
        """
        browser = self.login()
        browser.get(self.districtdomain.format('MyAccount_Student_PXP.aspx'))

        table = browser.find_element_by_class_name('info_tbl')
        rows = table.find_element_by_tag_name('tbody')

        raw_data = [[data.text for data in row.find_elements_by_tag_name(
            'td')] for row in rows.find_elements_by_tag_name('tr')]

        student_data = {}

        for info in raw_data[1]:
            student_data[info.split(
                '\n', 1)[0].replace(
                '\n', ' ')] = info.split('\n', 1)[1].replace('\n', ' ')

        browser.close()
        return student_data

    def getStudentInfo(self):
        """Gets other student information
        Returns:
            A dictionary with other information on the student
        """
        browser = self.login()
        browser.get(self.districtdomain.format('PXP_Student.aspx?AGU=0'))

        table = browser.find_element_by_class_name('info_tbl')
        rows = table.find_element_by_tag_name('tbody')

        raw_data = [[data.text for data in row.find_elements_by_tag_name(
            'td')] for row in rows.find_elements_by_tag_name('tr')]

        student_data = {}

        for info in raw_data[1]:
            student_data[info.split(
                '\n', 1)[0].replace(
                '\n', ' ')] = info.split('\n', 1)[1].replace('\n', ' ')

        return student_data

    def getSchoolInfo(self):
        """Gets information on the student's school
        Returns:
            A dictionary with information on the student's school
        """
        browser = self.login()
        browser.get(self.districtdomain.format(
            'PXP_SchoolInformation.aspx?AGU=0'))

        table = browser.find_element_by_class_name('info_tbl')
        rows = table.find_element_by_tag_name('tbody')
        raw_data = [[data.text for data in row.find_elements_by_tag_name(
            'td')] for row in rows.find_elements_by_tag_name('tr')]

        school_data = {}

        for row in raw_data:
            for info in row:
                school_data[info.split(
                    '\n', 1)[0].replace(
                    '\n', ' ')] = info.split('\n', 1)[1].replace('\n', ' ')

        return school_data

    def getReportCard(self):
        """Gets the student's last report card
        Returns:
            A list containing dictionaries with basic class
            information and the letter grade from the last report card
        """
        browser = self.login()
        browser.get(self.districtdomain.format('PXP_Grades.aspx?AGU=0'))

        table = browser.find_element_by_class_name('info_tbl')
        rows = table.find_element_by_tag_name('tbody')

        raw_data = [[data.text for data in row.find_elements_by_tag_name(
            'td')] for row in rows.find_elements_by_tag_name('tr')]

        raw_data.remove(raw_data[1])

        reportcard_data = []

        for classes in raw_data[1:]:
            this_class_data = {}
            for attribute in raw_data[0]:
                if attribute == 'Resources' or attribute == 'Room Name':
                    continue
                this_class_data[attribute] = classes[raw_data[0].index(
                    attribute)]
            reportcard_data.append(this_class_data)

        browser.close()
        return reportcard_data

    def getGradeBook(self):
        """Get's the student's current grades for this grading period
        Returns:
            A list containing dictionaries with basic class
            information and the current grading period's grades out of 100
        """
        browser = self.login()
        browser.get(self.districtdomain.format('PXP_Gradebook.aspx?AGU=0'))

        return self.parseGradeBook(browser)

    def getGradesbyGradingPeriod(self, grading_period):
        """Gets the student's current grades for the specified grading period
        Args:
            grading_period (int/ str): The grading period to get grades from
        Returns:
            A list containing dictionaries with basic class
            information and final grades from that grading period out of 100
        """
        browser = self.login()
        browser.get(self.districtdomain.format('PXP_Gradebook.aspx?AGU=0'))

        return self.parseGradeBook(browser)

    def getGradingInfobyPeriod(self, period):
        """Gets grading information on the class
        Args:
            period (int/ str): The period of the class
        Returns:
            Dictionary with a grading summary and recent assignments
        """
        browser = self.login()
        browser.get(self.districtdomain.format('PXP_Gradebook.aspx?AGU=0'))

        browser.find_element_by_xpath("//a[text()={}]".format(period)).click()
        tables = browser.find_elements_by_class_name('info_tbl')
        rows = tables[0].find_element_by_tag_name('tbody')

        raw_data = [[data.text for data in row.find_elements_by_tag_name(
            'td')] for row in rows.find_elements_by_tag_name('tr')]

        grading_data = {}
        grading_data['Summary'] = []

        for row in raw_data[1:]:
            this_assignment_data = {}
            for column in row:
                if column.replace('.', '', 1).isdigit():
                    this_assignment_data[raw_data[0]
                                         [row.index(column)]] = float(column)
                elif column.text.strip('%').replace('.', '', 1).isdigit():
                    this_assignment_data[raw_data[0][row.index(column)
                                                     ]] = float(column.strip('%')) / 100
                else:
                    this_assignment_data[raw_data[0]
                                         [row.index(column)]] = column
            grading_data['Summary'].append(this_assignment_data)

        rows = tables[1].find_element_by_tag_name('tbody')

        raw_data = [[data.text for data in row.find_elements_by_tag_name(
            'td')] for row in rows.find_elements_by_tag_name('tr')]

        grading_data['Assignments'] = []

        for row in raw_data[2:-1]:
            this_assignment_data = {}
            for column in row:
                if raw_data[1][row.index(column)] == 'Resources':
                    continue
                elif raw_data[1][row.index(column)] == 'Score':
                    continue
                this_assignment_data[raw_data[1][row.index(column)]] = column

            grading_data['Assignments'].append(this_assignment_data)

        browser.close()
        return grading_data

    def getCalendarbyMonth(self, month, year):
        """Get all assignments/ events in the calendar
        Args:
            month (int/ str): The month to get events from
            year (int/ str): The year to get events from
        Returns:
            Dictionary with a ;ist of dictionaries containing
            the events/ assignments for each day in the specified month
        """
        browser = self.login()
        browser.get(self.districtdomain.format('PXP_Calendar.aspx?AGU=0'))

        calendarDropDown = Select(browser.find_element_by_name('LB'))
        calendarDropDown.select_by_value('{}/1/{}'.format(month, year))

        cal = browser.find_element_by_id('cal_tbl')
        rows = cal.find_element_by_tag_name('tbody')

        raw_data = [[data.text for data in row.find_elements_by_tag_name(
            'td')] for row in rows.find_elements_by_tag_name('tr')]

        calendar_data = {}

        for week in raw_data[1:]:
            for date in week:
                if not date.strip():
                    continue
                elif int(date.split('\n')[0]) != len(calendar_data.keys()) + 1:
                    continue
                else:
                    this_date_data = date.split('\n')
                    calendar_data['{}/{}'.format(month,
                                                 this_date_data[0])] = this_date_data[1:]

        browser.close()
        return calendar_data

    def parseGradeBook(self, browser):
        "Internal function to reduce duplicate code"
        table = browser.find_element_by_class_name('info_tbl')
        rows = table.find_element_by_tag_name('tbody')

        raw_data = [[data.text for data in row.find_elements_by_tag_name(
            'td')] for row in rows.find_elements_by_tag_name('tr')]

        class_data = []

        for classes in raw_data[1:]:
            this_class_data = {}
            for attribute in raw_data[0]:
                if attribute != 'Resources':
                    this_class_data[attribute] = classes[raw_data[0].index(
                        attribute)]
                    if attribute.startswith('P'):
                        this_class_data[attribute] = float("".join(
                            i for i in classes[raw_data[0].index(
                                attribute)] if i in ".0123456789"))
            class_data.append(this_class_data)

        browser.close()

        return class_data


class RoboStudentVue:
    def __init__(self, username, password, districtdomain):
        """The StudentVue scraper object.
        Args:
            username (str): The username of the student portal account
            password (str): The password of the student portal account
            districtdomain (str): The domain name of your student portal
        """
        self.districtdomain = districtdomain
        if not self.districtdomain.startswith('https://'):
            self.districtdomain = 'https://' + self.districtdomain
        if not self.districtdomain.endswith('/'):
            self.districtdomain += '/'
        self.districtdomain = self.districtdomain + '{}'
        self.browser = RoboBrowser(parser='html5lib')
        self.browser.open(self.districtdomain.format(
            'Login_Student_PXP.aspx?regenerateSessionId=True'))
        form = self.browser.get_form(id='Form1')
        form['username'] = username
        form['password'] = password
        self.browser.submit_form(form)

    def getSchedule(self):
        """Gets the student's schedule
        Returns:
            A list containing dictionaries with basic information for each class
        """
        self.browser.open(self.districtdomain.format(
            'PXP_ClassSchedule.aspx?AGU=0'))

        rows = self.browser.parsed.find(
            'table', class_='info_tbl').find_all('tr')

        class_data = []

        for row in rows[1:]:
            this_class_data = {}
            for attribute in rows[0].find_all('td'):
                this_class_data[attribute.text] = row.find_all(
                    'td')[rows[0].find_all('td').index(attribute)].text
            class_data.append(this_class_data)

        return class_data

    def getStudentContactInfo(self):
        """Gets the student's contact information
        Returns:
            A dictionary with contact information on the student
        """
        self.browser.open(self.districtdomain.format(
            'MyAccount_Student_PXP.aspx'))

        rows = self.browser.parsed.find(
            'table', class_='info_tbl').find_all('tr')

        student_data = {}

        for data in rows[1].find_all('td'):
            try:
                student_data[data.contents[0].text] = data.contents[2].text
            except AttributeError:
                student_data[data.contents[0].text] = data.contents[2]

        return student_data

    def getStudentInfo(self):
        """Gets other student information
        Returns:
            A dictionary with other information on the student
        """
        self.browser.open(self.districtdomain.format('PXP_Student.aspx?AGU=0'))

        rows = self.browser.parsed.find(
            'table', class_='info_tbl').find_all('tr')

        student_data = {}

        for data in rows[1].find_all('td'):
            try:
                student_data[data.contents[0].text] = data.contents[2].text
            except AttributeError:
                student_data[data.contents[0].text] = data.contents[2]

        return student_data

    def getSchoolInfo(self):
        """Gets information on the student's school
        Returns:
            A dictionary with information on the student's school
        """
        self.browser.open(self.districtdomain.format(
            'PXP_SchoolInformation.aspx?AGU=0'))

        rows = self.browser.parsed.find(
            'table', class_='info_tbl').find_all('tr')

        school_data = {}

        for data in rows[1].find_all('td'):
            try:
                school_data[data.contents[0].text] = data.contents[2].text
            except AttributeError:
                school_data[data.contents[0].text] = data.contents[2]

        return school_data

    def getReportCard(self):
        """Gets the student's last report card
        Returns:
            A list containing dictionaries with basic class
            information and the letter grade from the last report card
        """
        self.browser.open(self.districtdomain.format('PXP_Grades.aspx?AGU=0'))

        rows = self.browser.parsed.find(
            'table', class_='info_tbl').find_all('tr')

        rows.remove(rows[1])

        reportcard_data = []

        for classes in rows[1:]:
            this_class_data = {}
            for attribute in rows[0].find_all('td'):
                if attribute.text == 'Resources':
                    continue
                this_class_data[attribute.text] = classes.find_all(
                    'td')[rows[0].find_all('td').index(attribute)].text
            reportcard_data.append(this_class_data)

        return reportcard_data

    def getGradeBook(self):
        """Get's the student's current grades for this grading period
        Returns:
            A list containing dictionaries with basic class
            information and the current grading period's grades out of 100
        """
        self.browser.open(self.districtdomain.format(
            'PXP_Gradebook.aspx?AGU=0'))

        return self.parseGradeBook()

    def getGradesbyGradingPeriod(self, grading_period):
        """Gets the student's current grades for the specified grading period
        Args:
            grading_period (int/ str): The grading period to get grades from
        Returns:
            A list containing dictionaries with basic class
            information and final grades from that grading period out of 100
        """
        self.browser.open(self.districtdomain.format(
            'PXP_Gradebook.aspx?AGU=0'))

        for link in self.browser.parsed.find_all('a'):
            if 'P{}'.format(grading_period) in link.text:
                self.browser.follow_link(link)
                break

        return self.parseGradeBook

    def getGradingInfobyPeriod(self, period):
        """Gets grading information on the class
        Args:
            period (int/ str): The period of the class
        Returns:
            Dictionary with a grading summary and recent assignments
        """
        self.browser.open(self.districtdomain.format(
            'PXP_Gradebook.aspx?AGU=0'))

        for link in self.browser.parsed.find_all('a'):
            if link.text == str(period):
                self.browser.follow_link(link)
                break

        grading_data = {}
        grading_data['Summary'] = []

        tables = self.browser.parsed.find_all('table', class_='info_tbl')
        rows = tables[0].find_all('tr')

        for row in rows[1:]:
            this_cat_data = {}
            for column in row.find_all('td'):
                if column.text.replace('.', '', 1).isdigit():
                    this_cat_data[rows[0].find_all('td')[row.find_all(
                        'td').index(column)].text] = float(column.text)
                elif column.text.strip('%').replace('.', '', 1).isdigit():
                    this_cat_data[rows[0].find_all('td')[row.find_all(
                        'td').index(column)].text] = float(column.text.strip('%')) / 100
                else:
                    this_cat_data[rows[0].find_all('td')[row.find_all(
                        'td').index(column)].text] = column.text

            grading_data['Summary'].append(this_cat_data)

        grading_data['Assignments'] = []

        rows = tables[1].find_all('tr')

        for row in rows[2:-1]:
            this_assignment_data = {}
            for column in row.find_all('td'):
                if rows[1].find_all('td')[row.find_all('td').index(column)].text == 'Resources':
                    continue
                elif rows[1].find_all('td')[row.find_all('td').index(column)].text == 'Score':
                    continue
                this_assignment_data[rows[1].find_all(
                    'td')[row.find_all('td').index(column)].text] = column.text

            grading_data['Assignments'].append(this_assignment_data)

        return grading_data

    def parseGradeBook(self):
        "Internal function to reduce duplicate code"
        rows = self.browser.parsed.find(
            'table', class_='info_tbl').find_all('tr')

        class_data = []

        for classes in rows[1:]:
            this_class_data = {}
            for attribute in rows[0].find_all('td'):
                if attribute.text != 'Resources':
                    this_class_data[attribute.text] = classes.find_all(
                        'td')[rows[0].find_all('td').index(attribute)].text
                    if attribute.text.startswith('P') or attribute.text == 'Spring' or attribute.text == 'Fall':
                        this_class_data[attribute.text] = float("".join(
                            i for i in classes.find_all('td')[rows[0].find_all('td').index(
                                attribute)].text if i in ".0123456789"))
            class_data.append(this_class_data)

        return class_data
