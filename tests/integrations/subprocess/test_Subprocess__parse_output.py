import pytest

from briefcase.integrations.subprocess import CommandOutputParseError, ParserError


def line_two_parser(data):
    try:
        return data.splitlines()[1]
    except IndexError:
        raise ParserError("Unable to parse line two")


def line_three_parser(data):
    try:
        return data.splitlines()[2]
    except IndexError:
        raise ParserError("Unable to parse line three")


def test_call(mock_sub, capsys):
    "A simple call to check_output will be invoked"

    mock_sub.parse_output(['hello', 'world'], output_parser=str)

    mock_sub._subprocess.check_output.assert_called_with(['hello', 'world'], text=True)
    assert capsys.readouterr().out == ""


def test_call_with_arg(mock_sub, capsys):
    "Any extra keyword arguments are passed through as-is to check_output"

    mock_sub.parse_output(['hello', 'world'], output_parser=str, extra_arg="asdf")

    mock_sub._subprocess.check_output.assert_called_with(
        ['hello', 'world'],
        extra_arg="asdf",
        text=True,
    )
    assert capsys.readouterr().out == ""


def test_call_with_parser_success(mock_sub, capsys):
    "Parser returns expected portion of check_output's output"

    output = mock_sub.parse_output(['hello', 'world'], output_parser=line_two_parser)

    mock_sub._subprocess.check_output.assert_called_with(["hello", "world"], text=True)
    assert output == "more output line 2"


def test_call_with_parser_error(mock_sub, capsys):
    "Parser errors on output from check_output"

    with pytest.raises(
            CommandOutputParseError,
            match="Unable to parse command output: Unable to parse line three"
    ):
        mock_sub.parse_output(['hello', 'world'], output_parser=line_three_parser)

    mock_sub._subprocess.check_output.assert_called_with(["hello", "world"], text=True)
    expected_output = (
        "\nCommand Output Parsing Error:\n"
        "    Unable to parse line three\n"
        "Command:\n"
        "    hello world\n"
        "Command Output:\n"
        "    some output line 1\n"
        "    more output line 2\n"
    )
    assert capsys.readouterr().out == expected_output


def test_text_eq_true_defaulting(mock_sub):
    "text should always be passed as True if text or universal_newlines is not explicitly provided"

    mock_sub.parse_output(['hello', 'world'], output_parser=str)
    mock_sub._subprocess.check_output.assert_called_with(["hello", "world"], text=True)


@pytest.mark.parametrize("setting", (True, False, None))
def test_text_eq_true_default_overriding(mock_sub, setting):
    "if text or universal_newlines is explicitly provided, those should override text=true default"

    mock_sub.parse_output(['hello', 'world'], output_parser=str, text=setting)
    mock_sub._subprocess.check_output.assert_called_with(["hello", "world"], text=setting)

    mock_sub.parse_output(['hello', 'world'], output_parser=str, universal_newlines=setting)
    mock_sub._subprocess.check_output.assert_called_with(["hello", "world"], universal_newlines=setting)
