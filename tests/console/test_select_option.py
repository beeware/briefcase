import pytest

from briefcase.console import select_option
from tests.utils import DummyConsole


def test_select_option():
    # Return '3' when prompted
    console = DummyConsole("3")

    options = {
        "first": "The first option",
        "second": "The second option",
        "third": "The third option",
        "fourth": "The fourth option",
    }
    result = select_option(options, input=console)

    # Input is requested once
    assert console.prompts == ["> "]

    # Alphabetically, option 3 will be "the second option"
    assert result == "second"


def test_select_option_list():
    """If select_option is given a list of tuples, they're presented as provided."""
    # Return '3' when prompted
    console = DummyConsole("3")

    options = [
        ("first", "The first option"),
        ("second", "The second option"),
        ("third", "The third option"),
        ("fourth", "The fourth option"),
    ]
    result = select_option(options, input=console)

    # Input is requested once
    assert console.prompts == ["> "]

    # The third option is the third option :-)
    assert result == "third"


def test_select_option_bad_input():
    # In order, return:
    #     blank
    #     'asdf'
    #     '10'
    #     '3'
    console = DummyConsole("", "asdf", "10", "3")

    options = {
        "first": "The first option",
        "second": "The second option",
        "third": "The third option",
        "fourth": "The fourth option",
    }
    result = select_option(options, input=console)

    # Input is requested five times; first four cause errors.
    assert console.prompts == ["> "] * 4

    # Alphabetically, option 3 will be "the second option"
    assert result == "second"


@pytest.mark.parametrize("default, expected_choice", [("1", "first"), ("3", "third")])
def test_select_option_default(default, expected_choice):
    """If select_option has a default, it is returned for no input."""
    # Return an empty response when prompted as though the user press entered
    console = DummyConsole("")

    options = [
        ("first", "The first option"),
        ("second", "The second option"),
        ("third", "The third option"),
        ("fourth", "The fourth option"),
    ]
    result = select_option(options, input=console, default=default)

    # Input is requested once
    assert console.prompts == ["> "]

    # The default option is returned
    assert result == expected_choice
