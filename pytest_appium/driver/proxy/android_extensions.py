import logging
from time import sleep
from contextlib import contextmanager

from pytest_appium.android.UIAutomator2 import UiSelector, UiScrollable
from pytest_appium.driver.proxy.proxy_mixin import register_proxy_mixin


log = logging.getLogger(__name__)


@register_proxy_mixin(name='android')
class AndroidUIAutomator2Mixin():

    def scroll_to_element_by_android_uiautomator(self, selector):
        assert isinstance(selector, (UiScrollable, UiSelector, UiCollection)), 'scroll to selector requires UiSelector object'
        return self.find_element_by_android_uiautomator(UiScrollable().scrollIntoView(selector))

    def find_element_by_android_uiautomator(self, selector):
        if isinstance(selector, (UiScrollable, UiSelector, UiCollection)):
            selector = str(selector)
        return self.__class__.find_element_by_android_uiautomator(self, selector)

    def find_text_on_page(self, text):
        return self.find_element_on_page(UiSelector().text(text))

    def find_description_on_page(self, description):
        return self.find_element_on_page(UiSelector().description(description))


@register_proxy_mixin(name='android')
class Gestures():
    def back(self):
        self.press_keycode(4)

    def home(self):
        self.press_keycode(3)

    def app_switcher(self):
        self.press_keycode(187)

    def background_app(self, sleep_seconds=0):
        # Don't use appium background_app() which restarts the app
        self.app_switcher()
        sleep(sleep_seconds)
        self._foreground_app()

    def _foreground_app(self):
        self.back()


@register_proxy_mixin(name='android')
class AndroidWebViewMixin():

    @property
    def webview_selector(self):
        return UiSelector().className('android.webkit.WebView')

    @property
    def webview_selector_child(self):
        return self.webview_selector.childSelector(UiSelector().className('android.view.View'))

    @property
    def webview_element(self):
        return self.find_element_on_page(self.webview_selector)

    def wait_for_webview(self, *args, **kwargs):
        assert self.capabilities.get('automationName') == 'UiAutomator2', 'WebView wait is only supported with UiAutomator2 driver'
        kwargs.setdefault('timeout', 30)
        assert self.wait_for(
            self.webview_selector_child.build(),
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
