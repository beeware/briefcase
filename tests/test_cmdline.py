import sys
from unittest import mock

import pytest

from briefcase import __version__, cmdline
from briefcase.commands import DevCommand, NewCommand, UpgradeCommand
from briefcase.console import Console, Log
from briefcase.exceptions import (
    InvalidFormatError,
    NoCommandError,
    ShowOutputFormats,
    UnsupportedCommandError,
)
from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand
from briefcase.platforms.macOS.app import macOSAppCreateCommand, macOSAppPublishCommand
from briefcase.platforms.windows.app import WindowsAppCreateCommand


@pytest.fixture
def logger() -> Log:
    return Log()


@pytest.fixture
def console() -> Console:
    return Console()


def do_cmdline_parse(args: list, logger: Log, console: Console):
    """Simulate process to parse command line."""
    Command, extra_cmdline = cmdline.parse_cmdline(args)
    cmd = Command(logger=logger, console=console)
    options = cmd.parse_options(extra=extra_cmdline)
    return cmd, options


def test_empty():
    """``briefcase`` returns basic usage."""
    with pytest.raises(NoCommandError, match=r"usage: briefcase") as excinfo:
        cmdline.parse_cmdline("".split())

    assert excinfo.value.msg.startswith(
        "usage: briefcase [-h] <command> [<platform>] [<format>] ...\n"
        "\n"
        "Package Python code for distribution.\n"
        "\n"
        "positional arguments:\n"
    )


def test_help_only():
    """``briefcase -h`` returns basic usage."""
    with pytest.raises(NoCommandError, match=r"usage: briefcase") as excinfo:
        cmdline.parse_cmdline("-h".split())

    assert excinfo.value.msg.startswith(
        "usage: briefcase [-h] <command> [<platform>] [<format>] ...\n"
        "\n"
        "Package Python code for distribution.\n"
        "\n"
        "positional arguments:\n"
    )


def test_version_only(capsys):
    """``briefcase -V`` returns current version."""
    with pytest.raises(SystemExit) as excinfo:
        cmdline.parse_cmdline("-V".split())

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Version is displayed.
    output = capsys.readouterr().out
    assert output == f"{__version__}\n"


def test_show_output_formats_only():
    """``briefcase -f`` returns basic usage as a command is needed."""
    with pytest.raises(NoCommandError, match=r"usage: briefcase") as excinfo:
        cmdline.parse_cmdline("-f".split())

    assert excinfo.value.msg.startswith(
        "usage: briefcase [-h] <command> [<platform>] [<format>] ...\n"
        "\n"
        "Package Python code for distribution.\n"
        "\n"
        "positional arguments:\n"
    )


def test_unknown_command():
    """``briefcase foobar`` fails as an invalid command."""
    with pytest.raises(SystemExit) as excinfo:
        cmdline.parse_cmdline("foobar".split())

    assert excinfo.value.code == 2
    assert excinfo.value.__context__.argument_name == "command"
    assert excinfo.value.__context__.message.startswith(
        "invalid choice: 'foobar' (choose from"
    )


def test_new_command(logger, console):
    """``briefcase new`` returns the New command."""
    cmd, options = do_cmdline_parse("new".split(), logger, console)

    assert isinstance(cmd, NewCommand)
    assert cmd.platform == "all"
    assert cmd.output_format is None
    assert cmd.input.enabled
    assert cmd.logger.verbosity == 1
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {"template": None}


def test_dev_command(monkeypatch, logger, console):
    """``briefcase dev`` returns the Dev command."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    cmd, options = do_cmdline_parse("dev".split(), logger, console)

    assert isinstance(cmd, DevCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format is None
    assert cmd.input.enabled
    assert cmd.logger.verbosity == 1
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {"appname": None, "update_dependencies": False, "run_app": True}


def test_upgrade_command(monkeypatch, logger, console):
    """``briefcase upgrade`` returns the upgrade command."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    cmd, options = do_cmdline_parse("upgrade".split(), logger, console)

    assert isinstance(cmd, UpgradeCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format is None
    assert cmd.input.enabled
    assert cmd.logger.verbosity == 1
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {
        "list_tools": False,
        "tool_list": [],
    }


def test_bare_command(monkeypatch, logger, console):
    """``briefcase create`` returns the macOS create app command."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    cmd, options = do_cmdline_parse("create".split(), logger, console)

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format == "app"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == 1
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}


@pytest.mark.skipif(sys.platform != "linux", reason="requires Linux")
def test_linux_default(logger, console):
    """``briefcase create`` returns the linux create appimage command on
    Linux."""

    cmd, options = do_cmdline_parse("create".split(), logger, console)

    assert isinstance(cmd, LinuxAppImageCreateCommand)
    assert cmd.platform == "linux"
    assert cmd.output_format == "appimage"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == 1
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}


@pytest.mark.skipif(sys.platform != "darwin", reason="requires macOS")
def test_macOS_default(logger, console):
    """``briefcase create`` returns the linux create appimage command on
    Linux."""

    cmd, options = do_cmdline_parse("create".split(), logger, console)

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format == "app"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == 1
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows")
def test_windows_default(logger, console):
    """``briefcase create`` returns the Windows create app command on
    Windows."""

    cmd, options = do_cmdline_parse("create".split(), logger, console)

    assert isinstance(cmd, WindowsAppCreateCommand)
    assert cmd.platform == "windows"
    assert cmd.output_format == "app"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == 1
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}


def test_bare_command_help(monkeypatch, capsys, logger, console):
    """``briefcase create -h`` returns the macOS create app command help."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    with pytest.raises(SystemExit) as excinfo:
        do_cmdline_parse("create -h".split(), logger, console)

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Help message is for default platform and format
    output = capsys.readouterr().out
    assert output.startswith(
        "usage: briefcase create macOS app [-h] [-v] [-V] [--no-input] [--log]\n"
        "\n"
        "Create and populate a macOS app.\n"
    )


def test_bare_command_version(capsys, logger, console):
    """``briefcase create -V`` returns the version."""
    with pytest.raises(SystemExit) as excinfo:
        do_cmdline_parse("create -V".split(), logger, console)

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Version is displayed.
    output = capsys.readouterr().out
    assert output == f"{__version__}\n"


def test_bare_command_show_formats(monkeypatch, logger, console):
    """``briefcase create -f`` returns an error indicating a platform is
    needed."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    with pytest.raises(ShowOutputFormats) as excinfo:
        do_cmdline_parse("create -f".split(), logger, console)

    assert excinfo.value.platform == "macOS"
    assert excinfo.value.default == "app"
    assert set(excinfo.value.choices) == {"xcode", "app"}


def test_command_unknown_platform(monkeypatch, logger, console):
    """``briefcase create foobar`` raises an unknown platform error."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    with pytest.raises(SystemExit) as excinfo:
        do_cmdline_parse("create foobar".split(), logger, console)

    assert excinfo.value.code == 2
    assert excinfo.value.__context__.argument_name == "platform"
    assert excinfo.value.__context__.message.startswith(
        "invalid choice: 'foobar' (choose from"
    )


def test_command_explicit_platform(monkeypatch, logger, console):
    """``briefcase create linux`` returns linux create app command."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    cmd, options = do_cmdline_parse("create linux".split(), logger, console)

    assert isinstance(cmd, LinuxAppImageCreateCommand)
    assert cmd.platform == "linux"
    assert cmd.output_format == "appimage"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == 1
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}


def test_command_explicit_platform_case_handling(monkeypatch, logger, console):
    """``briefcase create macOS`` returns macOS create app command."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    # This is all lower case; the command normalizes to macOS
    cmd, options = do_cmdline_parse("create macOS".split(), logger, console)

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format == "app"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == 1
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}


def test_command_explicit_platform_help(monkeypatch, capsys, logger, console):
    """``briefcase create macOS -h`` returns the macOS create app command
    help."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    with pytest.raises(SystemExit) as excinfo:
        do_cmdline_parse("create macOS -h".split(), logger, console)

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Help message is for default platform and format
    output = capsys.readouterr().out
    assert output.startswith(
        "usage: briefcase create macOS app [-h] [-v] [-V] [--no-input] [--log]\n"
        "\n"
        "Create and populate a macOS app.\n"
    )


def test_command_explicit_platform_show_formats(monkeypatch, logger, console):
    """``briefcase create macOS -f`` shows formats for the platform."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    with pytest.raises(ShowOutputFormats) as excinfo:
        do_cmdline_parse("create macOS -f".split(), logger, console)

    assert excinfo.value.platform == "macOS"
    assert excinfo.value.default == "app"
    assert set(excinfo.value.choices) == {"xcode", "app"}


def test_command_explicit_format(monkeypatch, logger, console):
    """``briefcase create macOS app`` returns the macOS create app command."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    cmd, options = do_cmdline_parse("create macOS app".split(), logger, console)

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format == "app"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == 1
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}


def test_command_unknown_format(monkeypatch, logger, console):
    """``briefcase create macOS foobar`` returns an invalid format error."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    expected_exc_regex = r"Invalid format 'foobar'; \(choose from: app, xcode\)"
    with pytest.raises(InvalidFormatError, match=expected_exc_regex):
        do_cmdline_parse("create macOS foobar".split(), logger, console)


def test_command_explicit_unsupported_format(monkeypatch, logger, console):
    """``briefcase create macOS homebrew`` raises an error because the format
    isn't supported (yet)"""
    # Mock the output formats to include a "homebrew" backend with no commands.
    monkeypatch.setattr(
        cmdline,
        "get_output_formats",
        mock.MagicMock(return_value={"homebrew": None}),
    )

    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    with pytest.raises(
        UnsupportedCommandError,
        match=r"The create command for the macOS homebrew format has not been implemented \(yet!\).",
    ):
        do_cmdline_parse("create macOS homebrew".split(), logger, console)


def test_command_explicit_format_help(monkeypatch, capsys, logger, console):
    """``briefcase create macOS app -h`` returns the macOS create app help."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    with pytest.raises(SystemExit) as excinfo:
        do_cmdline_parse("create macOS app -h".split(), logger, console)

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Help message is for default platform, but app format
    output = capsys.readouterr().out
    assert output.startswith(
        "usage: briefcase create macOS app [-h] [-v] [-V] [--no-input] [--log]\n"
        "\n"
        "Create and populate a macOS app.\n"
    )


def test_command_explicit_format_show_formats(monkeypatch, logger, console):
    """``briefcase create macOS app -f`` shows formats for the platform."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    with pytest.raises(ShowOutputFormats) as excinfo:
        do_cmdline_parse("create macOS app -f".split(), logger, console)

    assert excinfo.value.platform == "macOS"
    assert excinfo.value.default == "app"
    assert set(excinfo.value.choices) == {"xcode", "app"}


def test_command_disable_input(monkeypatch, logger, console):
    """``briefcase create --no-input`` disables console input."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    cmd, options = do_cmdline_parse("create --no-input".split(), logger, console)

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format == "app"
    assert not cmd.input.enabled
    assert cmd.logger.verbosity == 1
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}


def test_command_options(monkeypatch, capsys, logger, console):
    """Commands can provide their own arguments."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    # Invoke a command that is known to have its own custom arguments
    # (In this case, the channel argument for publication)
    cmd, options = do_cmdline_parse("publish macos app -c s3".split(), logger, console)

    assert isinstance(cmd, macOSAppPublishCommand)
    assert cmd.input.enabled
    assert cmd.logger.verbosity == 1
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {"channel": "s3"}


def test_unknown_command_options(monkeypatch, capsys, logger, console):
    """Commands can provide their own arguments."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    # Invoke a command but provide an option. that isn't defined
    with pytest.raises(SystemExit) as excinfo:
        do_cmdline_parse("publish macOS xcode -x foobar".split(), logger, console)

    # Normal exit due to displaying help
    assert excinfo.value.code == 2
    # Help message is for default platform and format
    output = capsys.readouterr().err

    assert output.startswith(
        "usage: briefcase publish macOS Xcode [-h] [-v] [-V] [--no-input] [--log]\n"
        "                                     [-c {s3}]\n"
        "briefcase publish macOS Xcode: error: unrecognized arguments: -x"
    )
