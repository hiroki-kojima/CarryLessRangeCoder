from os import path
from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'readme.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='CarryLessRangeCoder',
    version='1.0.1',
    url='https://github.com/hiroki-kojima/CarryLessRangeCoder',
    author='hiroki-kojima',
    author_email='hiroki.kojima.1997@gmail.com',
    description='Python implementation of carry-less range coder',
    packages=['carryless_rangecoder'],
    long_description=long_description,
)