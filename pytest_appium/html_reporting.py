import pytest
import json
from datetime import datetime


def _gather_app_strings(item, report, driver, summary, extra):
    """Add app_strings to the html report (if set in commandline)"""
    try:
        app_strings = driver.app_strings()
    except Exception as e:
        summary.append('WARNING: Failed to gather app_strings: {0}'.format(e))
        return

    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
        extra.append(pytest_html.extras.json(app_strings, 'app_strings'))

    app_string_keys = item.config.getoption('appium_debug_app_string_key')
    if app_string_keys:
        app_strings = {k: v for k, v in app_strings.items() if k in app_string_keys}
        summary.append('APP_STRINGS: {0}'.format(app_strings))


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

def _gather_video(item, report, driver, summary, extra):
    try:
        video = driver.stop_recording_screen()
    except Exception as e:
        summary.append('WARNING: Failed to gather video: {0}'.format(e))
        return
    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
        # add screenshot to the html report
        extra.append(pytest_html.extras.mp4(video, 'Video'))


def _gather_page_source(item, report, driver, summary, extra):
    try:
        page_source = driver.page_source
    except Exception as e:
        summary.append('WARNING: Failed to gather page_source: {0}'.format(e))
        return
    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
        # Add page source to the html report
        #   There is no `.xml(` output, so we create our own `.extra`
        extra.append(
            pytest_html.extras.extra(
                page_source, pytest_html.extras.FORMAT_TEXT,
                name='UI', mime_type='application/xml', extension='xml',
            )
        )


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
            extra.append(
                pytest_html.extras.text(
                    format_log(log), '%s Log' % name.title()
                )
            )


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



class AppiumReportPlugin(object):

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
                if 'app_strings' not in exclude:
                    _gather_app_strings(item, report, driver, summary, extra)
                if 'screenshot' not in exclude:
                    _gather_screenshot(item, report, driver, summary, extra)
                if 'video' not in exclude:
                    _gather_video(item, report, driver, summary, extra)
                if 'page_source' not in exclude:
                    _gather_page_source(item, report, driver, summary, extra)
                if 'logs' not in exclude:
                    pass  # log gathering on Android is very time-consuming,
                    # and seems to fail on Jenkins anyway
                    # _gather_logs(item, report, driver, summary, extra)
                item.config.hook.pytest_appium_capture_debug(item=item, report=report, extra=extra)
            item.config.hook.pytest_appium_runtest_makereport(item=item, report=report, summary=summary, extra=extra)
        if summary:
            report.sections.append(('pytest-appium', '\n'.join(summary)))
        report.extra = extra

