import copy
from datetime import datetime
import os
import sys

import pytest

from appium import webdriver


@pytest.fixture(scope='session', autouse=True)
def _environment(request, session_capabilities):
    """Provide additional environment details to pytest-html report"""
    config = request.config
    # add environment details to the pytest-html plugin
    #config._environment.append(('Driver', config.option.driver))
    # add capabilities to environment
    config._environment.extend([('Capability', '{0}: {1}'.format(
        k, v)) for k, v in session_capabilities.items()])
    #if config.option.driver == 'Remote':
    config._environment.append(
        ('Server', 'http://{0.appium_host}:{0.appium_port}'.format(config.option))
    )


@pytest.fixture(scope='session')
def session_capabilities(request, variables):
    """Returns combined capabilities from pytest-variables and command line (--capabilities)"""
    capabilities = variables.get('capabilities', {})
    for capability in request.config.getoption('capabilities'):
        capabilities[capability[0]] = capability[1]
    return capabilities


@pytest.fixture
def driver_kwargs(request, capabilities):
    """ """
    # Assertions of capabilitys should go here
    #appium_user = f'{0.appium_username}:{0.appium_access_key}@'
    kwargs = dict(
        command_executor='http://{0.appium_host}:{0.appium_port}/wd/hub'.format(request.config.option),
        desired_capabilities=capabilities,
        browser_profile=None,
        proxy=None,
        keep_alive=False,
    )
    return kwargs


@pytest.fixture
def driver_class(request):
    """Appium driver class"""
    return webdriver.Remote


@pytest.yield_fixture
def driver(request, driver_class, driver_kwargs):
    """Returns a AppiumDriver instance based on options and capabilities"""
    driver = driver_class(**driver_kwargs)

    #event_listener = request.config.getoption('event_listener')
    #if event_listener is not None:
    #    # Import the specified event listener and wrap the driver instance
    #    mod_name, class_name = event_listener.rsplit('.', 1)
    #    mod = __import__(mod_name, fromlist=[class_name])
    #    event_listener = getattr(mod, class_name)
    #    if not isinstance(driver, EventFiringWebDriver):
    #        driver = EventFiringWebDriver(driver, event_listener())

    request.node._driver = driver
    yield driver
    driver.quit()


@pytest.yield_fixture(scope='session')
def driver_session_(request, session_capabilities):
    """do not use this fixture directly as screenshots will not function"""
    _driver_class = driver_class(request)
    yield from driver(
        request,
        _driver_class,
        driver_kwargs(
            request,
            session_capabilities,
        )
    )
@pytest.yield_fixture
def driver_session(request, driver_session_):
    """Appium driver (session)"""
    request.node._driver = driver_session_  # Required to facilitate screenshots in html reports
    yield driver_session_


@pytest.yield_fixture
def appium(driver_session):
    """Appium driver instance for device specified in capabilities"""
    yield driver_session
