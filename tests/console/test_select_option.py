from unittest import mock

from briefcase.console import select_option


def test_select_option():
    # Return '3' when prompted
    mock_input = mock.MagicMock(return_value='3')

    options = {
        'first': 'The first option',
        'second': 'The second option',
        'third': 'The third option',
        'fourth': 'The fourth option',
    }
    result = select_option(options, input=mock_input)

    # Input is requested once
    assert mock_input.call_count == 1

    # Alphabetically, option 3 will be "the second option"
    assert result == 'second'


def test_select_option_bad_input():
    # In order, return:
    #     blank
    #     'asdf'
    #     '10'
    #     '3'
    mock_input = mock.MagicMock(side_effect=['', 'asdf', '10', '3'])

    options = {
        'first': 'The first option',
        'second': 'The second option',
        'third': 'The third option',
        'fourth': 'The fourth option',
    }
    result = select_option(options, input=mock_input)

    # Input is requested five times; first four cause errors.
    assert mock_input.call_count == 4

    # Alphabetically, option 3 will be "the second option"
    assert result == 'second'
