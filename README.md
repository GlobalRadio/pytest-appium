pytest-appium
=============

`pytest-appium` is a plugin for pytest that provides support for running Appium based tests.

It is inspired by [pytest-selenium](https://github.com/pytest-dev/pytest-selenium)

This package has a suite of additional utilities to augment the base Appium `driver` with additional modular functionality with python mixins


Setup
-----

pip requirements file
```
    git+http://GIT.SERVER.LOCATION/pytest-appium.git@master#egg=pytest-appium
```

pytest.ini
```
    [pytest]
    addopts = -p pytest_appium
```

python test example
```python
    from pytest_appium.android.UIAutomator2 import UiSelector, UiScrollable
    from pytest_appium.driver.proxy._enums import Direction

    @pytest.mark.platform('ios')
    def test_example(appium_extended, platform):
        el = appium_extended.find_element_on_page(
            UiSelector().resourceIdMatches('.*awesome_item'),
            direction=Direction.LEFT,
        )
        assert el.text == 'Example'
```

commandline example
```bash
    $(PYTHON_VENV)/bin/py.test \
        $(TEST_PATH) \
        --html=$(REPORT_PATH)/report.html \
        --junitxml=$(REPORT_PATH)/report.xml \
        --variables variables/pytest/android_emulator_local.json \
        --capability app $(APPIUM_APK_PATH)
```
for more commandline details use `pytest --help` under the heading `appium`


Features
--------

### HTML reports

[https://pypi.python.org/pypi/pytest-html/](pytest-html) for Appium tests.

Includes screenshot, page `XML` and full `logcat` dumps.


### Wait for startup conditions

Orchestration of service startup order is sometimes problematic.
On startup we can wait for a varity of conditions.
`pytest --help` for details

```
    --appium_wait_for_contition={appium,android_device_available}
                            Type of appium condition to wait for before beginning
                            first test
    --appium_wait_for_seconds=APPIUM_WAIT_FOR_SECONDS
                            Seconds to wait for an Appium server to become
                            available before raising an error.
```

Example of use in a `docker-compose.yml` waiting for android device.
```yaml
    command:
      - pytest
      ...
      - --appium_host=android-container
      - --appium_wait_for_seconds=90
      - --appium_wait_for_contition=android_device_available
      ...
```

Exampe of use in a `bash` script waiting for appium service to become active.
```bash
    ...
    (nohup node $(APPIUM_PATH) $(APPIUM_ARGS) > $(REPORT_FOLDER)/appium.log &)
    ...

    _env/bin/py.test \
        tests \
        ...
        --appium_host=localhost \
        --appium_wait_for_contition appium \
        --appium_wait_for_seconds 30 \
        ...

```

### pytest Markers for platforms

```python
    @pytest.mark.platform('ios')
    def test_ios(appium_extended):
        pass

    @pytest.mark.platform('android')
    def test_android(appium_extended):
        pass

    def test_both_ios_and_android(appium_extended):
        pass
```

### Python wrapper for expressing UiSelector syntax in python

Handling long android strings to compose UiSelectors is inflexible. A lightweight UiSelector python builder is provided

```python
    from pytest_appium.android.UIAutomator2 import UiSelector, UiScrollable

    # Create a UiSelector python builder
    selector = UiSelector().resourceIdMatches('.*filmstrip_list').childSelector(UiSelector().index(1))
    assert str(selector) == 'new UiSelector().resourceIdMatches(".*filmstrip_list").childSelector(new UiSelector().index(1))'

    # UiSelector objects can be used directly
    el = self.driver.find_element_by_android_uiautomator(selector)

    # UiSelectors can have segments modified/appended after creation
    selector.ui_objects[-1].childSelector(UiSelector().className('my_class'))
    assert str(selector) == 'new UiSelector().resourceIdMatches(".*filmstrip_list").childSelector(new UiSelector().index(1).childSelector(new UiSelector().className("my_class")))'
    self.driver.find_element_by_android_uiautomator(selector)
```

### Appium Driver Extensions

The base Appium [https://github.com/appium/python-client](python-client) `driver` supports base functions.
We sometimes want to add extra functionality to this `driver` for individual platforms.

We can transparently overlay extra Mixin's over the base `driver` object.

```python3
    from pytest_appium.driver.proxy.proxy_mixin import register_proxy_mixin

    @register_proxy_mixin(name='android')
    class MyAndroidDriverMixin():
        def new_thing(self, text):
            log.debug('my mixin method for android')
            # modify the selector in some cool way
            return self.find_element(*my_cool_selector_with_text)

    @register_proxy_mixin(name='ios')
    class MyIOSDriverMixin():
        def new_thing(self, text):
            log.debug('my mixin method for ios')
            # modify the selector in some cool way
            return self.find_element(*my_cool_selector_with_text)

    def test_my_mixin(appium_extended):
        el = appium_extended.new_thing('text of awesome')

    # The `appium` fixture can be used to get the base `driver` without mixin augmentation.
    @pytest.mark.xfail
    def test_my_mixin(appium):
        el = appium_extended.new_thing('text of awesome')

```

Omit the `name=''` to allow the mixin to augment all platforms.

Note: `dir(appium_extended)` will *NOT* reveal your additional mixin methods. They are invisible. (This could be improved in a future version)
