import logging
from time import sleep
from collections import namedtuple

from appium.webdriver.common.touch_action import TouchAction
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pytest_appium.android.UIAutomator2 import UiSelector, UiScrollable

from ._enums import Axis, Direction, Signum
from .proxy_mixin import register_proxy_mixin

log = logging.getLogger(__name__)


@register_proxy_mixin
class PlatformShortcutMixin():
    @property
    def platform(self):
        return (self.capabilities.get('platformName') or 'UNKNOWN').lower()


@register_proxy_mixin
class WebDriverWaitMixin():
    def wait_for(self, *args, timeout=5, expected_condition='presence_of_element_located', **kwargs):
        """
        https://seleniumhq.github.io/selenium/docs/api/py/webdriver_support/selenium.webdriver.support.expected_conditions.html#module-selenium.webdriver.support.expected_conditions
        """
        try:
            return WebDriverWait(self, timeout).until(getattr(EC, expected_condition)(*args, **kwargs))
        except TimeoutException:
            return None


@register_proxy_mixin
class AppiumElementHelperMixin():
    SwipeParams = namedtuple('SwipeParams', ('start_x', 'start_y', 'end_x', 'end_y'))

    def __init__(self, default_swipe_duration=200):
        self._default_swipe_duration = default_swipe_duration

    def find_element_safe(self, *args, **kwargs):
        assert len(args) == 2, 'find_element should be passed a tuple of (TYPE, LOCATOR)'
        try:
            return self.find_element(*args, **kwargs)
        except NoSuchElementException:
            log.debug(f'Unable to locate {args} {kwargs}')
            return None

    def get_element_bounds(self, locator=None):
        """
        Acquire a dict with pre-generated values for various x,y,width,height,midpoints.
        If a locator is not provided, the element falls back to the screen size.

        >>> from unittest.mock import MagicMock
        >>> t = AppiumElementHelperMixin(default_swipe_duration=300)
        >>> class MockElement():
        ...     size = {'width': 1000, 'height': 1000}
        ...     location = {'x': 500, 'y': 500}
        >>> t.find_element = MagicMock(return_value=MockElement())

        >>> t.get_element_bounds(locator=('MOCK_SELECTOR',))
        {'width': 1000, 'height': 1000, 'x': 500, 'y': 500, 'mid_x': 1000.0, 'mid_y': 1000.0, 'end_x': 1499, 'end_y': 1499}

        """
        if locator:
            el = self.find_element(*locator)
            el_size = el.size
            el_location = el.location
            bounds = {
                'width': el_size.get('width'),
                'height': el_size.get('height'),
                'x': el_location.get('x'),
                'y': el_location.get('y'),
            }
        else:
            bounds = {
                'width': self.get_window_size()['width'],
                'height': self.get_window_size()['height'],
                'x': 0,
                'y': 0,
            }
        bounds.update({
            'mid_x': bounds['x'] + bounds['width'] * 0.5,
            'mid_y': bounds['y'] + bounds['height'] * 0.5,
            'end_x': bounds['x'] + bounds['width'] - 1,
            'end_y': bounds['y'] + bounds['height'] - 1,
        })
        return bounds

    def swipe_element(self, direction=Direction.LEFT, swipe_distance=0.7, repeat=1, swipe_locator=None, duration_ms=None):  # , sleep_secs=0.5
        """
        Run the doctest with:
            _env/bin/pytest path/to/this_file.py --pdb

        >>> from unittest.mock import MagicMock
        >>> t = AppiumElementHelperMixin(default_swipe_duration=300)
        >>> t.swipe = MagicMock()
        >>> t.get_window_size = MagicMock(return_value={'width': 1000, 'height': 1000})

        >>> t.swipe_element(Direction.LEFT, swipe_distance=0.5)
        >>> t.swipe.assert_called_with(750, 500, 250, 500, duration=300)

        >>> t.swipe_element('right', swipe_distance=0.5)
        >>> t.swipe.assert_called_with(250, 500, 750, 500, duration=300)

        >>> t.swipe_element(Direction.UP, swipe_distance=0.5)
        >>> t.swipe.assert_called_with(500, 750, 500, 250, duration=300)

        >>> t.swipe_element(Direction.DOWN, swipe_distance=0.5)
        >>> t.swipe.assert_called_with(500, 250, 500, 750, duration=300)

        >>> t.swipe_element(Direction.LEFT, swipe_distance=0.8)
        >>> t.swipe.assert_called_with(900, 500, 100, 500, duration=300)

        """
        if isinstance(direction, str):
            direction = direction.upper()
            assert hasattr(Direction, direction), f'Unknown direction {direction}. Should be one of {Direction.__members__.keys()}'
            direction = getattr(Direction, direction)
        assert isinstance(direction, Direction)

        bounds = self.get_element_bounds(swipe_locator)

        center_point_of_moving_axis = bounds[f'mid_{direction.axis.value}']
        range_of_moving_axis = bounds[direction.axis.size]

        swipe_from = center_point_of_moving_axis - (range_of_moving_axis * (swipe_distance / 2))
        swipe_to = center_point_of_moving_axis + (range_of_moving_axis * (swipe_distance / 2))

        center_point_of_constant_axis = bounds[f'mid_{direction.axis.inverse.value}']

        swipe_params = self.SwipeParams(**{
            f'start_{direction.axis.value}': int(direction.signum.value(swipe_from, swipe_to)),
            f'end_{direction.axis.value}': int(direction.signum.inverse.value(swipe_from, swipe_to)),
            f'start_{direction.axis.inverse.value}': int(center_point_of_constant_axis),
            f'end_{direction.axis.inverse.value}': int(center_point_of_constant_axis),
        })

        assert all(map(lambda x: x >= 0, swipe_params)), f'All swipe co-ordinates should be positive {swipe_params}'
        for i in range(0, repeat):
            self.swipe(*swipe_params, duration=duration_ms or self._default_swipe_duration)
            #sleep(float(sleep_secs))

    def find_element_on_page(self, locator, swipe_direction=Direction.UP, max_swipes=4, **kwargs):
        """
        Largely reproduces the role/concept of the Android `UiScrollable` but it platform dependent.
        """
        if isinstance(locator, (UiScrollable, UiSelector)):
            locator = locator.build()
        kwargs.setdefault('swipe_distance', 0.35)
        def _find(swipe_direction):
            for i in range(0, max_swipes):
                el = self.find_element_safe(*locator)
                if el:
                    return el
                else:
                    log.debug(f'Swiping again to locate {locator}')
                    self.swipe_element(direction=swipe_direction, **kwargs)
                el = self.find_element_safe(*locator)
                if el:
                    return el
        el = _find(swipe_direction)
        if not el and isinstance(swipe_direction, Direction):
             el = _find(swipe_direction.inverse)
        return el


@register_proxy_mixin
class Gestures():
    def tap_a_point(self, x=0, y=0):
        """ Click A Point does not work as it uses action.press() """
        action = TouchAction(self)
        try:
            action.tap(x=float(x), y=float(y)).perform()
        except Exception:
            assert False, "Can't click on a point at (%s,%s)" % (x, y)


@register_proxy_mixin
class Orientation():
    def get_orientation(self):
        return self.orientation

    def set_orientation(self, orientation):
        self.orientation = orientation

    def remember_original_orientation(self):
        self.original_orientation = self.get_orientation()

    def restore_original_orientation(self):
        self.set_orientation(self.original_orientation)

    # TODO: Why is it locking device rotation?
    # https://discuss.appium.io/t/android-set-the-orientation-but-app-refused-to-rotate/3200/6
    # ???The problem was in Android app code. Devs should set orientation reliance to user not to censor.
    # adb shell content insert --uri content://settings/system --bind name:s:accelerometer_rotation --bind value:i:1
    # https://developer.android.com/reference/android/R.attr.html#screenOrientation
    def rotate_device(self):
        try:
            self.set_orientation(
                'LANDSCAPE' if self.get_orientation() == 'PORTRAIT' else 'PORTRAIT')
            sleep(0.5)
        except WebDriverException:
            print(
                'Device does not support orientation change. '
                'This failed operation has probably left the app in an odd state.')
