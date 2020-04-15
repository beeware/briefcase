from briefcase.console import InputWrapper


def test_input_wrapper_default_constructor():
    input_wrapper = InputWrapper()
    assert input_wrapper.enabled


def test_input_wrapper_constructor_with_enabled_true():
    input_wrapper = InputWrapper(enabled=True)
    assert input_wrapper.enabled


def test_input_wrapper_constructor_with_enabled_false():
    input_wrapper = InputWrapper(enabled=False)
    assert not input_wrapper.enabled


def test_input_wrapper_enable(disabled_input_wrapper):
    assert not disabled_input_wrapper.enabled

    disabled_input_wrapper.enable()

    assert disabled_input_wrapper.enabled


def test_input_wrapper_multiple_enable(disabled_input_wrapper):
    assert not disabled_input_wrapper.enabled

    disabled_input_wrapper.enable()
    disabled_input_wrapper.enable()
    disabled_input_wrapper.enable()

    assert disabled_input_wrapper.enabled


def test_input_wrapper_disable(input_wrapper):
    assert input_wrapper.enabled

    input_wrapper.disable()

    assert not input_wrapper.enabled


def test_input_wrapper_multiple_disable(input_wrapper):
    assert input_wrapper.enabled

    input_wrapper.disable()
    input_wrapper.disable()
    input_wrapper.disable()

    assert not input_wrapper.enabled
