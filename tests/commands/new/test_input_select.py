from unittest import mock


def test_valid_selection(new_command):
    "If the user picks a valid selection, it is returned"
    new_command.input = mock.MagicMock(return_value='2')

    value = new_command.input_select(
        intro="Some introduction",
        variable="my variable",
        options=[
            'first',
            'second',
            'third',
        ]
    )

    assert new_command.input.call_count == 1
    new_command.input.assert_called_with("""
Select one of the following:

    [1] first
    [2] second
    [3] third

My Variable [1]: """)
    assert value == "second"


def test_invalid_selection(new_command):
    "If the user picks a valid selection, it is returned"
    new_command.input = mock.MagicMock(side_effect=['4', '0', 'asdf', '3'])

    value = new_command.input_select(
        intro="Some introduction",
        variable="my variable",
        options=[
            'first',
            'second',
            'third',
        ]
    )

    assert new_command.input.call_count == 4
    new_command.input.assert_called_with("""
Select one of the following:

    [1] first
    [2] second
    [3] third

My Variable [1]: """)
    assert value == "third"


def test_default_selection(new_command):
    "If the user picks a valid selection, it is returned"
    new_command.input = mock.MagicMock(return_value='')

    value = new_command.input_select(
        intro="Some introduction",
        variable="my variable",
        options=[
            'first',
            'second',
            'third',
        ]
    )

    assert new_command.input.call_count == 1
    new_command.input.assert_called_with("""
Select one of the following:

    [1] first
    [2] second
    [3] third

My Variable [1]: """)
    assert value == "first"


def test_prompt_capitalization(new_command):
    "The prompt is correctly capitalized"
    new_command.input = mock.MagicMock(return_value='2')

    new_command.input_select(
        intro="Some introduction",
        variable="user's URL",
        options=[
            'first',
            'second',
            'third',
        ]
    )

    new_command.input.assert_called_with("""
Select one of the following:

    [1] first
    [2] second
    [3] third

User's URL [1]: """)
