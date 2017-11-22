from setuptools import setup
from os import path

_here = path.dirname(path.abspath(__file__))
_readme = open(path.join(_here, 'README.md')).read()

setup(
    name='pytest-appium',
    description='',
    long_description=_readme,
    version='0.0.1',
    url='http://git.int.thisisglobal.com/interactive/pytest-appium',
    author='Global',
    author_email=' leicestersquare-interactive-developers@global.com',
    license='MIT',
    platform='any',
    py_modules=['pytest_appium'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords='appium pytest'
)
