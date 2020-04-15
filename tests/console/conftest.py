from unittest import mock

import pytest

from briefcase.console import InputWrapper


@pytest.fixture
def input_wrapper():
    input_wrapper = InputWrapper()
    input_wrapper._actual_input = mock.MagicMock()
    return input_wrapper


@pytest.fixture
def disabled_input_wrapper():
    input_wrapper = InputWrapper(enabled=False)
    input_wrapper._actual_input = mock.MagicMock()
    return input_wrapper
