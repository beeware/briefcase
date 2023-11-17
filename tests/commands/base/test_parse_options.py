import pytest

from briefcase.console import LogLevel


def test_parse_options_no_overrides(base_command):
    """Command line options are parsed if provided without overrides."""
    options, overrides = base_command.parse_options(
        extra=(
            "-x",
            "wibble",
            "-r",
            "important",
        )
    )

    assert options == {
        "extra": "wibble",
        "mystery": None,
        "required": "important",
    }
    assert overrides == {}
    assert base_command.input.enabled
    assert base_command.logger.verbosity == LogLevel.INFO


def test_parse_options_with_overrides(base_command):
    """Command line options and overrides are parsed if provided."""
    options, overrides = base_command.parse_options(
        extra=(
            "-x",
            "wibble",
            "-r",
            "important",
            "-C",
            "width=10",
            "-C",
            "height=20",
        )
    )

    assert options == {
        "extra": "wibble",
        "mystery": None,
        "required": "important",
    }
    assert overrides == {
        "width": 10,
        "height": 20,
    }
    assert base_command.input.enabled
    assert base_command.logger.verbosity == LogLevel.INFO


@pytest.mark.parametrize(
    "verbosity, log_level",
    [
        ("", LogLevel.INFO),
        ("-v", LogLevel.VERBOSE),
        ("-vv", LogLevel.DEBUG),
        ("-vvv", LogLevel.DEEP_DEBUG),
        ("-vvvv", LogLevel.DEEP_DEBUG),
        ("-vvvvv", LogLevel.DEEP_DEBUG),
    ],
)
def test_verbosity(base_command, verbosity, log_level):
    """The logging level is set correctly for the verbosity."""
    base_command.parse_options(extra=filter(None, ("-r", "default", verbosity)))

    assert base_command.logger.verbosity == log_level


def test_missing_option(base_command, capsys):
    """If a required option isn't provided, an error is raised."""
    with pytest.raises(SystemExit) as excinfo:
        base_command.parse_options(extra=("-x", "wibble"))

    # Error code for a missing required option
    assert excinfo.value.code == 2
    # Error message about missing option is displayed
    err = capsys.readouterr().err
    assert "the following arguments are required: -r/--required" in err


def test_unknown_option(other_command, capsys):
    """If an unknown command is provided, it raises an error."""
    with pytest.raises(SystemExit) as excinfo:
        other_command.parse_options(extra=("-y", "because"))

    # Error code for an unknown option
    assert excinfo.value.code == 2
    # Error message about unknown option is displayed
    err = capsys.readouterr().err
    assert "unrecognized arguments: -y because" in err


def test_no_options(other_command, capsys):
    """If a command doesn't define options, any option is an error."""
    with pytest.raises(SystemExit) as excinfo:
        other_command.parse_options(extra=("-x", "wibble"))

    # Error code for an unknown option
    assert excinfo.value.code == 2
    # Error message about unknown option is displayed
    err = capsys.readouterr().err
    assert "unrecognized arguments: -x wibble" in err
