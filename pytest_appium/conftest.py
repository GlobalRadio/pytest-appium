import logging
import copy
from datetime import datetime
import os
import sys
import urllib.error
import time
import datetime
from functools import partial
from itertools import filterfalse

import pytest
from appium import webdriver

from ._utils import get_json, post_json
from .driver.proxy.proxy_mixin import proxy
from .driver.proxy import appium_extensions
from .driver.proxy import android_extensions
from .driver.proxy import ios_extensions


log = logging.getLogger(__name__)


@pytest.fixture(scope='session', autouse=True)
def _environment(request, session_capabilities):
    """Provide additional environment details to pytest-html report"""
    config = request.config
    # add environment details to the pytest-html plugin
    #config._environment.append(('Driver', config.option.driver))
    # add capabilities to environment
    if not hasattr(config, '_environment'):
        log.warn('pytest.config has no _environment')
        return
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


def driver_kwargs(request, capabilities):
    """ """
    # Assertions of capabilitys should go here
    #appium_user = f'{0.appium_username}:{0.appium_access_key}@'
    kwargs = dict(
        command_executor='http://{0.appium_host}:{0.appium_port}'.format(request.config.option),
        desired_capabilities=capabilities,
        browser_profile=None,
        proxy=None,
        keep_alive=False,
    )
    return kwargs


def driver_class(request):
    """Appium driver class"""
    return webdriver.Remote

@pytest.fixture
def driver_class_fixture(request):
    return driver_class(request)


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


def _appium_is_device_available(appium_wd_api_endpoint, desiredCapabilities={}, appNameKey=''):
    """
    Problem:
        We cant ask appium how many devices are attacked from it's 'wd' api.
    Solution:
        Attempt to launch a package that deliberately does not exist.
        If a device is found it will try to launch this non existent app.
        We can detect that error state tried to load that app.
        If it 'did' try to load it, we know we attached to a device.
    Example Outputs:
        curl -H "Content-Type: application/json" -X POST -d '{"desiredCapabilities":{"platformName": "Android", "deviceName":"Android Emulator", "appPackage":"NOT_REAL"}}' http://devandroid02.lq.int.thisisglobal.com:4723/wd/hub/session
        {'status': 13, 'value': {'message': 'An unknown server-side error occurred while processing the command. Original error: Could not find a connected Android device.'}, 'sessionId': None}
        {'status': 13, 'value': {'message': "An unknown server-side error occurred while processing the command. Original error: Cannot stop and clear NOT_REAL. Original error: Error executing adbExec. Original error: 'Command '/usr/local/Caskroom/android-sdk/3859397/platform-tools/adb -P 5037 -s emulator-5554 shell pm clear NOT_REAL' exited with code 1'; Stderr: 'Failed'; Code: '1'"}, 'sessionId': None}
    """
    response = post_json(
        url=f'''{appium_wd_api_endpoint}/session''',
        data={"desiredCapabilities": desiredCapabilities},
    )
    return desiredCapabilities[appNameKey] in response.get('value', {}).get('message', '')

appium_is_device_available_android = partial(
    _appium_is_device_available,
    desiredCapabilities={
        "platformName": "Android",
        "deviceName": "Android Emulator",
        "appPackage": "NOT_REAL",
        "clearSystemFiles": True,
    },
    appNameKey='appPackage',
)

appium_is_device_available_ios = partial(
    _appium_is_device_available,
    desiredCapabilities={
        "platformName": "iOS",
        "deviceName": "iPhone Simulator",
        "automationName": "XCUITest",
        "bundleId": "NOT_REAL",
    },
    appNameKey='bundleId',
)

APPIUM_WAIT_FOR = {
    'appium': lambda appium_url: get_json(f"""{appium_url}/status""").get('value').get('build').get('version'),
    'android_device_available': appium_is_device_available_android,
    #'ios_device_available': appium_is_device_available_ios,
}

@pytest.fixture(scope='session')
def driver_session_(request, session_capabilities):
    """
    Appium Session
    Created from --capabilities
    (do not use this fixture directly as report screenshots will not function)
    """
    _driver_class = driver_class(request)
    _driver_kwargs = driver_kwargs(request, session_capabilities)

    appium_url = _driver_kwargs['command_executor']

    # Wait for Appium
    def wait_for_appium():
        wait_for_condition = request.config.option.appium_wait_for_condition
        seconds_to_wait = request.config.option.appium_wait_for_seconds
        if not seconds_to_wait or not wait_for_condition:
            return
        assert wait_for_condition in APPIUM_WAIT_FOR
        expire_datetime = datetime.datetime.now() + datetime.timedelta(seconds=seconds_to_wait)
        while datetime.datetime.now() <= expire_datetime:
            try:
                if APPIUM_WAIT_FOR[wait_for_condition](appium_url):
                    log.debug('Android Device (apparently) ready: Waiting for further grace period')
                    time.sleep(request.config.option.appium_wait_grace_for_seconds)
                    return
            except Exception:
                pass
            log.debug(f'Waiting on {wait_for_condition} for {seconds_to_wait} for Appium server{appium_url}')
            time.sleep(2)
        raise Exception(f'Server not ready. Failed to wait on {wait_for_condition} for {seconds_to_wait} seconds for Appium server {appium_url}')
    wait_for_appium()

    try:
        yield from driver(request, _driver_class, _driver_kwargs)
    except urllib.error.URLError:
        raise Exception(f"""Unable to connect to Appium server {appium_url}""")


@pytest.fixture
def driver_session(request, driver_session_):
    """
    Appium Session
    """
    request.node._driver = driver_session_  # Required to facilitate screenshots in html reports
    yield driver_session_
    #driver_session_.reset()


@pytest.fixture
def appium(driver_session):
    """Alias for driver_session"""
    yield driver_session


@pytest.fixture
def appium_extended(appium):
    appium = proxy(appium)  # Apply generic mixins over appium
    appium = proxy(appium, appium.platform)  # Apply platform specific mixins
    return appium


def pytest_collection_modifyitems(config, items):
    """
    https://docs.pytest.org/en/latest/example/markers.html#custom-marker-and-command-line-option-to-control-test-runs
    https://docs.pytest.org/en/latest/writing_plugins.html#_pytest.hookspec.pytest_collection_modifyitems

    Process platform marker:
        @pytest.mark.platform('android')
        def test_example():
            pass
    """

    # Filter tests that are not targeted for this platform
    current_platform = config._variables.get('capabilities',{}).get('platformName','').lower()
    def select_test(item):
        platform_marker = item.get_closest_marker("platform")
        if platform_marker and platform_marker.args and current_platform:
            test_platform_specified = platform_marker.args[0].lower()
            if test_platform_specified != current_platform:
                return False
        return True
    config.hook.pytest_deselected(items=filterfalse(select_test, items))
    items[:] = filter(select_test, items)
