import pytest


def test_parse_options(base_command):
    "Command line options are parsed if provided"
    options = base_command.parse_options(
        extra=(
            '-x', 'wibble',
            '-r', 'important'
        )
    )

    assert options == {
        'verbosity': 1,
        'extra': "wibble",
        'mystery':  None,
        'required': "important",
    }


def test_missing_option(base_command, capsys):
    "If a required option isn't provided, an error is raised"
    with pytest.raises(SystemExit) as excinfo:
        base_command.parse_options(
            extra=('-x', 'wibble')
        )

    # Error code for a missing required option
    assert excinfo.value.code == 2
    # Error message about missing option is displayed
    err = capsys.readouterr().err
    assert "the following arguments are required: -r/--required" in err


def test_unknown_option(other_command, capsys):
    "If an unknown command is provided, it rasises an error"
    with pytest.raises(SystemExit) as excinfo:
        other_command.parse_options(
            extra=('-y', 'because')
        )

    # Error code for a unknown option
    assert excinfo.value.code == 2
    # Error message about unknown option is displayed
    err = capsys.readouterr().err
    assert "unrecognized arguments: -y because" in err


def test_no_options(other_command, capsys):
    "If a command doesn't define options, any option is an error"
    with pytest.raises(SystemExit) as excinfo:
        other_command.parse_options(
            extra=('-x', 'wibble')
        )

    # Error code for a unknown option
    assert excinfo.value.code == 2
    # Error message about unknown option is displayed
    err = capsys.readouterr().err
    assert "unrecognized arguments: -x wibble" in err
