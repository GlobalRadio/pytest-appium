import os

from .conftest import *

def pytest_configure(config):
    if hasattr(config, 'slaveinput'):
        return  # xdist slave
    # http://doc.pytest.org/en/latest/writing_plugins.html#optionally-using-hooks-from-3rd-party-plugins
    if config.pluginmanager.hasplugin('html'):
            #import pdb ; pdb.set_trace()
            from .html_reporting import AppiumReportPlugin
            #from .pytest_appium import *
            config.pluginmanager.register(AppiumReportPlugin())
    config.addinivalue_line(
        'markers', 'capabilities(kwargs): add or change existing '
        'capabilities. specify capabilities as keyword arguments, for example '
        'capabilities(foo=''bar'')')


def pytest_addhooks(pluginmanager):
    from . import hooks
    method = getattr(pluginmanager, 'add_hookspecs', None)
    if method is None:
        method = pluginmanager.addhooks
    method(hooks)


def pytest_addoption(parser):
    _capture_choices = ('never', 'failure', 'always')
    parser.addini(
        'appium_capture_debug',
        help='when debug is captured {0}'.format(_capture_choices),
        default=os.getenv('APPIUM_CAPTURE_DEBUG', 'failure'),
    )
    parser.addini(
        'appium_exclude_debug',
        help='debug to exclude from capture',
        default=os.getenv('APPIUM_EXCLUDE_DEBUG'),
    )

    group = parser.getgroup('appium', 'appium')
    group.addoption('--appium_host', metavar='str', default='localhost', help='')
    group.addoption('--appium_port', metavar='str', default='4723', help='')
    group.addoption('--appium_wait_for_contition', choices=APPIUM_WAIT_FOR.keys(), help='Type of appium condition to wait for before begining first test')
    group.addoption('--appium_wait_for_seconds', type=int, default=0, help='Seconds to wait for an Appium server to become available before raising an error.')
    group.addoption('--appium_debug_app_string_key', metavar='str', action='append', default=[], help='Strings to extract on failure for html report')
    group.addoption(
        '--capability',
        action='append',
        default=[],
        dest='capabilities',
        metavar=('key', 'value'),
        nargs=2,
        help='device capabilities.'  # http://pytest-selenium.readthedocs.io/en/latest/user_guide.html#capabilities-files
    )
    group.addoption(
        '--event-listener',
        metavar='str',
        help='appium eventlistener class, e.g. package.module.EventListenerClassName.'
    )


def pytest_report_header(config, startdir):
    """return a string to be displayed as header info for terminal reporting."""
    capabilities = config.getoption('capabilities')
    if capabilities:
        return 'capabilities: {0}'.format(capabilities)
