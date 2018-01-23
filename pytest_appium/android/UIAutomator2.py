try:
    from appium.webdriver.common.mobileby import MobileBy
except ImportError:
    class MobileBy():
        ANDROID_UIAUTOMATOR = '-android uiautomator'

"""
https://bitbar.com/how-to-get-started-with-ui-automator-2-0/
"""


class _PythonUIAutomatorBuilderMixin():
    """
    Designed to be used as Mixin.
    The example below is a raw unmodified output.
    See other examples for actual use cases.

    >>> str(_PythonUIAutomatorBuilderMixin().text('moose'))
    '.text("moose")'

    >>> str(
    ...     _PythonUIAutomatorBuilderMixin()
    ...     .text('moose')
    ...     .child(
    ...         _PythonUIAutomatorBuilderMixin()
    ...         .childText('more')
    ...     )
    ... )
    '.text("moose").child(.childText("more"))'
    """

    def __init__(self):
        self.segments = {}  # Python3.6 guarantees dict iteration in insertion order
        self.PREPROCESSORS = {}

    def __str__(self):
        # Should be overridden
        return self._render_args()

    def _render_args(self):
        return ''.join(self._render_arg(method_name, arg) for method_name, arg in self.segments.items())

    def _render_arg(self, method_name, args):
        """
        Special processors for some methods else fallthough string
        """
        def _format_arg_as_java_string(arg):
            #if arg.__class__.__name__ == UiSelector.__name__:
            if isinstance(arg, self.__class__):
                return str(arg)
            if isinstance(arg, str):
                return f'''"{arg}"'''
            if isinstance(arg, bool):
                return 'true' if arg else 'false'
            raise Exception(f'unknown arg type to build java uiselector {args}')

        def _preprocess_arg(arg):
            return self.PREPROCESSORS.get(method_name, lambda x: x)(arg)

        return f'''.{method_name}({', '.join(map(_format_arg_as_java_string, map(_preprocess_arg, args)))})'''

    def __getattribute__(self, method_name):
        """
        Use the 'builder' pattern to construct a 'java' command from 'python' object access
        """
        try:
            return super().__getattribute__(method_name)
        except AttributeError as ae:
            def _add_segment(*args):
                self.segments[method_name] = args
                return self
            return _add_segment


class UiSelector(_PythonUIAutomatorBuilderMixin):
    """
    https://developer.android.com/reference/android/support/test/uiautomator/UiSelector.html
    https://github.com/appium/python-client#finding-elements-by-android-uiautomator-search

    example of raw driver call:
        self.driver.find_element_by_android_uiautomator('new UiSelector().description("Animation")')

    example of 'UiSelector' use:
        UiSelector().description('Animation').build()
        UiSelector().description('Animation', resource_id='expected_id').build()
        UiSelector().text('Hello', resource_id='text_element_id').build()
        UiSelector().className('bob').build()

    >>> UiSelector().text('Test').build()
    ('-android uiautomator', 'new UiSelector().text("Test")')

    >>> UiSelector(app_package='test.app.com').resourceId('title').className('name').build()
    ('-android uiautomator', 'new UiSelector().resourceId("test.app.com:id/title").className("name")')

    >>> UiSelector().childSelector(UiSelector().className('test')).build()
    ('-android uiautomator', 'new UiSelector().childSelector(new UiSelector().className("test"))')
    """

    def __init__(self, app_package=None):
        _PythonUIAutomatorBuilderMixin.__init__(self)

        self.app_package = app_package

        def _augment_resourceId(resource_id):
            if self.app_package and not resource_id.startswith(self.app_package):
                return f'''{app_package}:id/{resource_id}'''
            return resource_id
        self.PREPROCESSORS = {
            'resourceId': _augment_resourceId,
        }

    def __str__(self):
        return f'''new UiSelector(){self._render_args()}'''

    def build(self):
        return (MobileBy.ANDROID_UIAUTOMATOR, self.__str__())


class UiScrollable(_PythonUIAutomatorBuilderMixin):
    """
    https://developer.android.com/reference/android/support/test/uiautomator/UiScrollable.html

    >>> str(
    ...     UiScrollable(UiSelector().className('container')).scrollTextIntoView('My Title')
    ... )
    'new UiScrollable(new UiSelector().className("container")).scrollTextIntoView("My Title")'
    """

    def __init__(self, uiselector_container):
        _PythonUIAutomatorBuilderMixin.__init__(self)
        assert uiselector_container
        self.uiselector_container = uiselector_container

    def __str__(self):
        return f'''new UiScrollable({self.uiselector_container}){self._render_args()}'''
