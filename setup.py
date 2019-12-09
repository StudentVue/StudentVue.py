from setuptools import setup
import os

setup(
    name='studentvue-old',
    packages=['studentvue'],
    version='1.0',
    description='Python Scraper for StudentVue Portals',
    author='Kai Chang',
    url='https://github.com/kajchang/studentvuescraper',
    license='MIT',
    long_description=open(os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'README.md')).read(),
    long_description_content_type="text/markdown",
    install_requires=['robobrowser']
)
