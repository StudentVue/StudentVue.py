from robobrowser import RoboBrowser

class StudentVue:
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
