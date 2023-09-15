import subprocess
from unittest.mock import ANY

import pytest

from briefcase.integrations.subprocess import CommandOutputParseError, ParseError


def splitlines_parser(data):
    """A test parser that returns the input data, split by line."""
    return data.splitlines()


def second_line_parser(data):
    """A test parser that returns the second line of input."""
    try:
        return data.splitlines()[1]
    except IndexError:
        raise ParseError("Input does not contain 2 lines")


def third_line_parser(data):
    """A test parser that returns the third line of input."""
    try:
        return data.splitlines()[2]
    except IndexError:
        raise ParseError("Input does not contain 3 lines")


def test_call(mock_sub, capsys, sub_check_output_kw):
    """A simple call to check_output will be invoked."""

    output = mock_sub.parse_output(splitlines_parser, ["hello", "world"])

    mock_sub._subprocess.check_output.assert_called_with(
        ["hello", "world"],
        **sub_check_output_kw,
    )
    assert capsys.readouterr().out == ""
    assert output == ["some output line 1", "more output line 2"]


def test_call_with_arg(mock_sub, capsys, sub_check_output_kw):
    """Any extra keyword arguments are passed through as-is to check_output."""

    output = mock_sub.parse_output(
        splitlines_parser,
        ["hello", "world"],
        extra_kw="extra",
    )

    mock_sub._subprocess.check_output.assert_called_with(
        ["hello", "world"],
        extra_kw="extra",
        **sub_check_output_kw,
    )
    assert capsys.readouterr().out == ""
    assert output == ["some output line 1", "more output line 2"]


def test_call_with_parser_success(mock_sub, capsys, sub_check_output_kw):
    """Parser returns expected portion of check_output's output."""

    output = mock_sub.parse_output(second_line_parser, ["hello", "world"])

    mock_sub._subprocess.check_output.assert_called_with(
        ["hello", "world"],
        **sub_check_output_kw,
    )

    assert output == "more output line 2"


def test_call_with_parser_error(mock_sub, capsys, sub_check_output_kw):
    """Parser errors on output from check_output."""

    with pytest.raises(
        CommandOutputParseError,
        match="Unable to parse command output: Input does not contain 3 lines",
    ):
        mock_sub.parse_output(third_line_parser, ["hello", "world"])

    mock_sub._subprocess.check_output.assert_called_with(
        ["hello", "world"],
        **sub_check_output_kw,
    )

    expected_output = (
        "\n"
        "Command Output Parsing Error:\n"
        "    Input does not contain 3 lines\n"
        "Command:\n"
        "    hello world\n"
        "Command Output:\n"
        "    some output line 1\n"
        "    more output line 2\n"
    )
    assert capsys.readouterr().out == expected_output


@pytest.mark.parametrize(
    "in_kwargs, kwargs",
    [
        ({}, {"text": True, "encoding": ANY, "errors": "backslashreplace"}),
        ({"text": True}, {"text": True, "encoding": ANY, "errors": "backslashreplace"}),
        ({"text": False}, {"text": False}),
        ({"universal_newlines": False}, {"text": False}),
        (
            {"universal_newlines": True},
            {"text": True, "encoding": ANY, "errors": "backslashreplace"},
        ),
    ],
)
def test_text_eq_true_default_overriding(mock_sub, in_kwargs, kwargs):
    """If text or universal_newlines is explicitly provided, those should override
    text=true default and universal_newlines should be converted to text."""

    mock_sub.parse_output(splitlines_parser, ["hello", "world"], **in_kwargs)

    mock_sub._subprocess.check_output.assert_called_with(
        ["hello", "world"],
        stderr=subprocess.STDOUT,
        **kwargs,
    )
