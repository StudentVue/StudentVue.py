# Student Vue Scraper
Python Package for Scraping StudentVue Portals with Selenium/ Robobrowser

# How to Use

```pip install studentvue```

There are two implementations of the scraper, one written using Selenium, and one written using RoboBrowser. They are almost identical, though RoboBrowser is faster, while Selenium can scrape the calendar and RoboBrowser cannot.

## For Selenium:

Download the Chrome driver from the [official site](https://sites.google.com/a/chromium.org/chromedriver/downloads).

```from studentvue.scraper import StudentVue```

Create a StudentVue object with your username, password, and the domain name of your StudentVue student portal. The program will use ```/usr/local/bin/chromedriver``` as the specified path for the Chrome driver as a default, you can specify a different one by including the ```driverpath``` parameter.

```sv = StudentVue('username', 'password', 'domain name', driverpath='path/to/driver')```

## For Robobrowser:
    
```from studentvue.scraper import RoboStudentVue```

```sv = RoboStudentVue('username', 'password', 'domain name')```

## Scraper Usage

The current functions of the both StudentVue classes are ```getSchedule()```, ```getStudentContactInfo()```, ```getStudentInfo()```, ```getSchoolInfo()```, ```getReportCard()```, ```getGradeBook()```, ```getGradesbyGradingPeriod(grading_period)``` and ```getGradingInfobyPeriod()```. The selenium version additionally has ```getCalendarbyMonth(month, year)```.

```getSchedule()``` returns a list of dictionaries with basic class information:
```
[
    {
        "Period": "1",
        "Course Title": "Computer Programming",
        "Room Name": "999",
        "Teacher": "Someone"
    }, ...]
```

```getStudentContactInfo()``` returns a dictionary with contact information on the student:
```
{
    "Name": "Kid, Some",
    "User ID": "somekid",
    "Home Address": "Some Where Street, Some City, Some State, 99999",
    "Mail Address": "Same as Home Address",
    "Phone Numbers": "Home: 999-999-999"
}
```

```getStudentInfo()``` returns a dictionary with some other information on the student:
```
{
    "Student Name": "Some J. Kid",
    "Student No": "32562395",
    "Gender": "Male",
    "Grade": "9"
}
```

```getSchoolInfo()``` returns a dictionary with some information on the school:
```
{
    "Principal": "Someone",
    "School Name": "Some HS",
    "Address": "Some Where Street, Some City, Some State, 99999",
    "Phone": "999-999-999",
    "Fax": "999-999-999",
    "Website URL": "https://some-school-website/"
}
```

```getReportCard()``` returns a list of dictionaries with class information and your grade from the last report card:
```
[
    {
        "Period": "1",
        "Course Title": "Computer Programming",
        "Teacher": "Someone",
        "Marks": "A"
    }, ...]
```

```getGradeBook()``` is similar, but returns numbers out of 100 instead of letters, and returns the latest grades from this grading period, opposed to grades from the last report card. Additionally, it sometimes includes the overall grade for the season/ semester/ trimester:
```
[
    {
        "Period": "1",
        "Course Title": "Computer Programming",
        "Teacher": "Someone",
        "P6": 95.54,
        "Spring": 96.67
    }, ...]
```

```getGradesbyGradingPeriod(grading_period)``` takes a grading period as a parameter and returns the final grade for that grading period, out of 100, in the same format as ```getGradeBook()```:
```
[
    {
        "Period": "1",
        "Course Title": "Computer Programming",
        "Teacher": "Someone",
        "P1": 97.42
    }, ...]
```

```getGradingInfobyPeriod(period)``` takes a period as a parameter and returns a dictionary with a grading overview and individual assignment grades:
```
{
    "Summary": [
        {
            "Assignment Type": "Classwork",
            "Weight": 0.05,
            "Points": 566.0,
            "Points Possible": 450.0,
            "Average": 0.0629
        }, ...
    ],
    "Assignments": [
        {
            "Date": "05/22/2018",
            "Assignment": "Chapter 14 Test",
            "Assignment Type": "Tests and Quizzes",
            "Score Type": "Raw Score",
            "Points": "3.50/5.00",
            "Notes": " "
        }, ...
    ]
}
```

```getCalendarbyMonth(month, year)``` takes a month and year as parameters and returns a dictionary with a list of dictionaries containing assignments for each day in the specified month:
```
{
    "5/1": [
        "World History : Ch. 18, 3 (p.578-582), Q #6, 7 & 8 - Score: 4",
    ], ...
}
```
