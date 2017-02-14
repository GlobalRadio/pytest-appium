#from .pytest_appium import *  # noqa
#from .plugin import *

def pytest_configure(config):
    if hasattr(config, 'slaveinput'):
        return  # xdist slave
    config.addinivalue_line(
        'markers', 'capabilities(kwargs): add or change existing '
        'capabilities. specify capabilities as keyword arguments, for example '
        'capabilities(foo=''bar'')')
    # http://doc.pytest.org/en/latest/writing_plugins.html#optionally-using-hooks-from-3rd-party-plugins
    if config.pluginmanager.hasplugin('html'):
            #import pdb ; pdb.set_trace()
            from .pytest_appium import AppiumPlugin
            #from .pytest_appium import *
            config.pluginmanager.register(AppiumPlugin())
