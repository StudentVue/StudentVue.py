# StudentVue API
![travis](https://travis-ci.com/kajchang/StudentVue.svg?branch=master)
![PyPI version](https://badge.fury.io/py/studentvue.svg)

This repository provides a easy way to access data from StudentVue portals in Python programs.

This project recently transitioned to using the SOAP API from the app instead of the web-based one. Using the SOAP API is much faster, consistent, and more lightweight. However, the APIs are not compatible, so if you need compatibility the web-based one, run `pip install studentvue==1.3.2`.

## Logging In

`pip install studentvue` or clone / download the repository and `python setup.py install`.

```python
from studentvue import StudentVue
sv = StudentVue('username', 'password', 'domain name') 
```

## Documentation

You can read some basic docs [here](https://kajchang.github.io/StudentVue/StudentVue.html).

## Bugs and Contributing

The content and formatting of pages may vary from district to district, so the same parsing strategies might fail. If you find an instance of this, or have a general improvement you can [raise a new issue](https://github.com/kajchang/StudentVue/issues/new) and/or [open a pull request](https://github.com/kajchang/StudentVue/compare).

## Ports

C# - [axiomaticTwist/StudentVueAPI](https://github.com/axiomaticTwist/StudentVueAPI)
