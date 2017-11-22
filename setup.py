from distutils.core import setup
from os import path

_here = path.dirname(path.abspath(__file__))

setup(
    name='pytest-appium',
    description='PyTest bindings for Appium',
    version='0.0.1',
    #py_modules=['pytest_appium'],
    packages=['pytest_appium'],
    long_description=open(path.join(_here, 'README.md')).read(),

    #url='http://git.int.thisisglobal.com/interactive/pytest-appium',
    #author='Global',
    #author_email=' leicestersquare-interactive-developers@global.com',
    #license='MIT',
    #platform='any',
    #classifiers=[
    #    'Development Status :: 3 - Alpha',
    #    'Programming Language :: Python',
    #    'Programming Language :: Python :: 3',
    #    'Programming Language :: Python :: 3.5',
    #    'Intended Audience :: Developers',
    #    'License :: OSI Approved :: MIT License',
    #    'Topic :: Software Development :: Libraries',
    #    'Topic :: Software Development :: Libraries :: Python Modules'
    #],
    #keywords='appium pytest'
)
