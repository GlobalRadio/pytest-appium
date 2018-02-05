import logging
from time import sleep

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

    def wait_for_webview(self, *args, **kwargs):
        kwargs.setdefault('timeout', 20)
        webview_selector = UiSelector().className('android.webkit.WebView')
        assert self.find_element(*UiScrollable().scrollIntoView(webview_selector).build())
        assert self.wait_for(
            webview_selector.childSelector(UiSelector().className('android.view.View')).build(),
            *args,
            **kwargs,
        )
