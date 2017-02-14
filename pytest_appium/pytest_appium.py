import copy
from datetime import datetime
import os
import sys

import pytest

from appium import webdriver


# Fixtures ---------------------------------------------------------------------


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
    """Returns combined capabilities from pytest-variables and command line"""
    capabilities = variables.get('capabilities', {})
    for capability in request.config.getoption('capabilities'):
        capabilities[capability[0]] = capability[1]
    return capabilities


@pytest.fixture
def driver_kwargs(request, capabilities):
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
    request.node._driver = driver_session_  # Required to facilitate screenshots in html reports
    yield driver_session_


@pytest.yield_fixture
def appium(driver_session):
    """Alias for driver"""
    yield driver_session


# pytest -----------------------------------------------------------------------


def _gather_url(item, report, driver, summary, extra):
    try:
        url = driver.current_url
    except Exception as e:
        summary.append('WARNING: Failed to gather URL: {0}'.format(e))
        return
    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
        # add url to the html report
        extra.append(pytest_html.extras.url(url))
    summary.append('URL: {0}'.format(url))


def _gather_screenshot(item, report, driver, summary, extra):
    try:
        screenshot = driver.get_screenshot_as_base64()
    except Exception as e:
        summary.append('WARNING: Failed to gather screenshot: {0}'.format(e))
        return
    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
        # add screenshot to the html report
        extra.append(pytest_html.extras.image(screenshot, 'Screenshot'))


def _gather_html(item, report, driver, summary, extra):
    try:
        html = driver.page_source
        #if not PY3:
        #    html = html.encode('utf-8')
    except Exception as e:
        summary.append('WARNING: Failed to gather HTML: {0}'.format(e))
        return
    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
        # add page source to the html report
        extra.append(pytest_html.extras.text(html, 'HTML'))


def _gather_logs(item, report, driver, summary, extra):
    try:
        types = driver.log_types
    except Exception as e:
        # note that some drivers may not implement log types
        summary.append('WARNING: Failed to gather log types: {0}'.format(e))
        return
    for name in types:
        try:
            log = driver.get_log(name)
        except Exception as e:
            summary.append('WARNING: Failed to gather {0} log: {1}'.format(
                name, e))
            return
        pytest_html = item.config.pluginmanager.getplugin('html')
        if pytest_html is not None:
            extra.append(pytest_html.extras.text(
                format_log(log), '%s Log' % name.title()))


def format_log(log):
    timestamp_format = '%Y-%m-%d %H:%M:%S.%f'
    entries = [u'{0} {1[level]} - {1[message]}'.format(
        datetime.utcfromtimestamp(entry['timestamp'] / 1000.0).strftime(
            timestamp_format), entry).rstrip() for entry in log]
    log = '\n'.join(entries)
    #if not PY3:
    #    log = log.encode('utf-8')
    return log


def split_class_and_test_names(nodeid):
    """Returns the class and method name from the current test"""
    names = nodeid.split('::')
    names[0] = names[0].replace('/', '.')
    names = [x.replace('.py', '') for x in names if x != '()']
    classnames = names[:-1]
    classname = '.'.join(classnames)
    name = names[-1]
    return (classname, name)



class AppiumPlugin(object):

    def pytest_addhooks(self, pluginmanager):
        from . import hooks
        method = getattr(pluginmanager, 'add_hookspecs', None)
        if method is None:
            method = pluginmanager.addhooks
        method(hooks)

    def pytest_report_header(self, config, startdir):
        """return a string to be displayed as header info for terminal reporting."""
        #driver = config.getoption('driver')
        #if driver is not None:
        #    return 'driver: {0}'.format(driver)
        pass

    @pytest.mark.hookwrapper
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        summary = []
        extra = getattr(report, 'extra', [])
        driver = getattr(item, '_driver', None)
        xfail = hasattr(report, 'wasxfail')
        failure = (report.skipped and xfail) or (report.failed and not xfail)
        when = item.config.getini('appium_capture_debug').lower()
        capture_debug = when == 'always' or (when == 'failure' and failure)
        if driver is not None:
            if capture_debug:
                exclude = item.config.getini('appium_exclude_debug').lower()
                if 'url' not in exclude:
                    _gather_url(item, report, driver, summary, extra)
                if 'screenshot' not in exclude:
                    _gather_screenshot(item, report, driver, summary, extra)
                if 'html' not in exclude:
                    _gather_html(item, report, driver, summary, extra)
                if 'logs' not in exclude:
                    _gather_logs(item, report, driver, summary, extra)
                item.config.hook.pytest_appium_capture_debug(
                    item=item, report=report, extra=extra)
            item.config.hook.pytest_appium_runtest_makereport(
                item=item, report=report, summary=summary, extra=extra)
        if summary:
            report.sections.append(('pytest-appium', '\n'.join(summary)))
        report.extra = extra

    def pytest_addoption(self, parser):
        _capture_choices = ('never', 'failure', 'always')
        parser.addini('appium_capture_debug',
                    help='when debug is captured {0}'.format(_capture_choices),
                    default=os.getenv('APPIUM_CAPTURE_DEBUG', 'failure'))
        parser.addini('appium_exclude_debug',
                    help='debug to exclude from capture',
                    default=os.getenv('APPIUM_EXCLUDE_DEBUG'))

        group = parser.getgroup('appium', 'appium')
        group._addoption('--appium_username', help='', metavar='str', default='')
        group._addoption('--appium_access_key', help='', metavar='str', default='')
        group._addoption('--appium_host', help='', metavar='str', default='localhost')
        group._addoption('--appium_port', help='', metavar='str', default='4723')

        #group._addoption('--driver',
        #                 choices=SUPPORTED_DRIVERS,
        #                 help='webdriver implementation.',
        #                 metavar='str')
        #group._addoption('--driver-path',
        #                 metavar='path',
        #                 help='path to the driver executable.')
        group._addoption(
            '--capability',
            action='append',
            default=[],
            dest='capabilities',
            metavar=('key', 'value'),
            nargs=2,
            help='additional capabilities.'  # http://pytest-selenium.readthedocs.io/en/latest/user_guide.html#capabilities-files
        )
        group._addoption(
            '--event-listener',
            metavar='str',
            help='appium eventlistener class, e.g. package.module.EventListenerClassName.'
        )
