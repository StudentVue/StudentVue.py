# StudentVue API
![travis](https://travis-ci.org/kajchang/StudentVue.svg?branch=master)
![PyPI version](https://badge.fury.io/py/studentvue.svg)

This repository provides a easy way to access data from StudentVue portals in Python programs.

## Logging In

`pip install studentvue` or clone / download the repository and `python setup.py install`.

```python
from studentvue import StudentVue
sv = StudentVue('username', 'password', 'domain name') 
```

## Methods

```python
>>> classes = sv.getClasses()
>>> classes
[
    'Period 2 CCSS Algebra 2A Taught by XXX XXX in Room XXX with a Grade of XX.X%',
    'Period 3 Chemistry A H Taught by XXX XXX in Room XXX with a Grade of XX.X%',
    ...
    'Period 7 AP Euro Hist A Taught by XXX XXX in Room XXX with a Grade of XX.X%',
    'Period 8 PE 2A Taught by XXX XXX in Room XXX with a Grade of XX.X%'
]

# classes and teachers are both objects

>>> classes[0].room
XXX

>>> classes[0].teacher.email
XXX@XXX.XXX
```

```python
>>> sv.getStudentInfo()
{
    'Student Name': 'XXXXX',
    'Student No': 'XXXXXX',
    'Gender': 'Male',
    'Grade': '10'
}
```

```python
>>> sv.getSchoolInfo()
# Principal, if supplied, will also be converted to a Teacher object
{
    'Principal': Andrew Ishibashi,
    'School Name': 'Lowell HS',
    'Address': '1101 Eucalyptus DrSan Francisco, CA 94132',
    'Phone': '415-759-2730',
    'Fax': '415-759-2742',
    'Website URL': 'https://lhs-sfusd-ca.schoolloop.com/'
}
```

## Bugs and Contributing

The content and formatting of pages may vary from district to district, so the same parsing strategies might fail. If you find an instance of this, or have a general improvement you can [raise a new issue](https://github.com/kajchang/StudentVue/issues/new) and/or [open a pull request](https://github.com/kajchang/StudentVue/compare).

## TODO

- Finish Scraper

- Write tests
