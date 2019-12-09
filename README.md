# StudentVue API
![travis](https://travis-ci.com/kajchang/StudentVue.svg?branch=master)
![PyPI version](https://badge.fury.io/py/studentvue.svg)

This repository provides a easy way to access data from StudentVue portals in Python programs.

Note:

If this library isn't updating properly, try explictly installing the latest version (e.g. `pip3 install studentvue==1.2.1`) to fix this issue in the future.

If you're getting an [AttributeError](https://github.com/kajchang/StudentVue/issues/12) when trying to log in, this might mean that your school is on an older version of StudentVue. Try uninstalling this library (`pip uninstall studentvue`) and installing `studentvue-old` (`pip uninstall studentvue-old`).

`studentvue-old` is not maintained and has a different API, but there is some [minimal documentation](https://github.com/kajchang/StudentVue/tree/old-version).

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

## TODO

- Finish Scraper

- Write tests
