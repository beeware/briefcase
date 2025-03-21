import pytest

from tests.utils import DummyConsole


@pytest.mark.parametrize(
    "user_input_val",
    ["true", "TRUE", "t", "T", "yes", "YES", "y", "Y", "1", "on", "ON"],
)
def test_true_values(user_input_val):
    console = DummyConsole()
    assert console.parse_boolean(user_input_val) is True


@pytest.mark.parametrize(
    "user_input_val",
    ["false", "FALSE", "f", "F", "no", "NO", "n", "N", "0", "off", "OFF"],
)
def test_false_values(user_input_val):
    console = DummyConsole()
    assert console.parse_boolean(user_input_val) is False


@pytest.mark.parametrize("user_input_val", ["maybe", "2", "", "help"])
def test_invalid_values(user_input_val):
    console = DummyConsole()
    with pytest.raises(ValueError):
        console.parse_boolean(user_input_val)


@pytest.mark.parametrize(
    "user_input_val, expected",
    [("         yEs ", True), ("nO          ", False), ("    YEs", True)],
)
def test_whitespace(user_input_val, expected):
    console = DummyConsole()
    assert console.parse_boolean(user_input_val) is expected
