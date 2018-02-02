from os import path
from setuptools import setup, find_packages


_here = path.dirname(path.abspath(__file__))


setup(
    name='pytest-appium',
    description='Plugin for running Appium with pytest ',
    version='0.0.2',
    packages=find_packages(),
    long_description=open(path.join(_here, 'README.md')).read(),
    install_requires=[
        'pytest',
        'pytest-html',
        'Appium-Python-Client',
        'wrapt',
    ],
    url='http://git.int.thisisglobal.com/interactive/pytest-appium',
    author='Global',
    author_email='leicestersquare-interactive-developers@global.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Pytest',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords=[
        'appium',
        'pytest',
        'py.test',
        'webqa',
        'qa',
    ],
)
