import logging
from contextlib import contextmanager

from appium.webdriver.common.mobileby import MobileBy as By

from pytest_appium.driver.proxy.proxy_mixin import register_proxy_mixin


log = logging.getLogger(__name__)


@register_proxy_mixin(name='ios')
class IOSWebViewMixin():

    def wait_for_webview(self, *args, **kwargs):
        kwargs.setdefault('timeout', 30)
        assert self.wait_for(
            (By.CLASS_NAME, 'XCUIElementTypeWebView'),
            *args,
            **kwargs,
        )

    @contextmanager
    def webview_context(self, context_name='WEBVIEW'):
        current_context_name = self.current_context
        target_context_name = (context for context in self.contexts if context_name in context).__iter__().__next__()
        assert target_context_name, 'Unable to find {context_name} in available contexts {self.contexts}'
        self.switch_to.context(target_context_name)
        yield None
        self.switch_to.context(current_context_name)
