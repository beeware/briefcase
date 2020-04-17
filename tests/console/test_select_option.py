from briefcase.console import select_option
from tests.commands.utils import DummyConsole


def test_select_option():
    # Return '3' when prompted
    input_wrapper = DummyConsole('3')

    options = {
        'first': 'The first option',
        'second': 'The second option',
        'third': 'The third option',
        'fourth': 'The fourth option',
    }
    result = select_option(options, input=input_wrapper)

    # Input is requested once
    assert input_wrapper.prompts == ['> ']

    # Alphabetically, option 3 will be "the second option"
    assert result == 'second'


def test_select_option_bad_input():
    # In order, return:
    #     blank
    #     'asdf'
    #     '10'
    #     '3'
    input_wrapper = DummyConsole('', 'asdf', '10', '3')

    options = {
        'first': 'The first option',
        'second': 'The second option',
        'third': 'The third option',
        'fourth': 'The fourth option',
    }
    result = select_option(options, input=input_wrapper)

    # Input is requested five times; first four cause errors.
    assert input_wrapper.prompts == ['> '] * 4

    # Alphabetically, option 3 will be "the second option"
    assert result == 'second'
