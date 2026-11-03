import logging
from contextlib import contextmanager

from appium.webdriver.common.appiumby import AppiumBy as By

from pytest_appium._utils import wait_for
from pytest_appium.driver.proxy.proxy_mixin import register_proxy_mixin


log = logging.getLogger(__name__)


@register_proxy_mixin(name='ios')
class IOSWebViewMixin():

    @property
    def webview_contexts(self, context_name='WEBVIEW'):
        return tuple(context for context in self.contexts if context_name in context)

    def wait_for_webview(self, *args, **kwargs):
        kwargs.setdefault('timeout', 30)
        wait_for(func_attempt=lambda: self.webview_contexts, trys=10)
        assert self.wait_for(
            (By.CLASS_NAME, 'XCUIElementTypeWebView'),
            *args,
            **kwargs,
        )

    @contextmanager
    def webview_context(self):
        current_context_name = self.current_context
        target_context_name = self.webview_contexts.__iter__().__next__()
        assert target_context_name, 'Unable to find {context_name} in available contexts {self.contexts}'
        self.switch_to.context(target_context_name)
        yield None
        self.switch_to.context(current_context_name)
