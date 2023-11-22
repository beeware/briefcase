import shlex
import sys
from unittest import mock

import pytest

from briefcase import __version__, cmdline
from briefcase.commands import DevCommand, NewCommand, UpgradeCommand
from briefcase.console import Console, Log, LogLevel
from briefcase.exceptions import (
    InvalidFormatError,
    NoCommandError,
    UnsupportedCommandError,
)
from briefcase.platforms.linux.system import LinuxSystemCreateCommand
from briefcase.platforms.macOS.app import (
    macOSAppCreateCommand,
    macOSAppPublishCommand,
    macOSAppRunCommand,
)
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
    options, overrides = cmd.parse_options(extra=extra_cmdline)
    return cmd, options, overrides


def test_empty():
    """``briefcase`` returns basic usage."""
    with pytest.raises(NoCommandError, match=r"usage: briefcase") as excinfo:
        cmdline.parse_cmdline("".split())

    assert excinfo.value.msg.startswith(
        "usage: briefcase [-h] <command> [<platform>] [<format>] ...\n"
        "\n"
        "Briefcase is a tool for converting a Python project into a standalone native\n"
        "application for distribution.\n"
        "\n"
        "Commands:\n"
    )


def test_help_only():
    """``briefcase -h`` returns basic usage."""
    with pytest.raises(NoCommandError, match=r"usage: briefcase") as excinfo:
        cmdline.parse_cmdline("-h".split())

    assert excinfo.value.msg.startswith(
        "usage: briefcase [-h] <command> [<platform>] [<format>] ...\n"
        "\n"
        "Briefcase is a tool for converting a Python project into a standalone native\n"
        "application for distribution.\n"
        "\n"
        "Commands:\n"
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


def test_unknown_command():
    """``briefcase foobar`` fails as an invalid command."""
    with pytest.raises(SystemExit) as excinfo:
        cmdline.parse_cmdline("foobar".split())

    assert excinfo.value.code == 2
    assert excinfo.value.__context__.argument_name == "command"
    assert excinfo.value.__context__.message.startswith(
        "invalid choice: 'foobar' (choose from"
    )


@pytest.mark.parametrize(
    "cmdline, expected_options, expected_overrides",
    [
        (
            "new",
            {
                "template": None,
                "template_branch": None,
                "project_overrides": None,
            },
            {},
        ),
        (
            "new --template=path/to/template --template-branch=experiment -C version=\\'1.2.3\\' -C other=42",
            {
                "template": "path/to/template",
                "template_branch": "experiment",
                "project_overrides": None,
            },
            {
                "version": "1.2.3",
                "other": 42,
            },
        ),
    ],
)
def test_new_command(logger, console, cmdline, expected_options, expected_overrides):
    """``briefcase new`` returns the New command."""
    cmd, options, overrides = do_cmdline_parse(shlex.split(cmdline), logger, console)

    assert isinstance(cmd, NewCommand)
    assert cmd.platform == "all"
    assert cmd.output_format is None
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == expected_options
    assert overrides == expected_overrides


# Common tests for dev and run commands.
def dev_run_parameters(command):
    return [
        (f"{command} {args}", expected, overrides)
        for args, expected, overrides in [
            ("", {}, {}),
            ("-r", {"update_requirements": True}, {}),
            (
                "-r -C version=\\'1.2.3\\' -C other=42",
                {"update_requirements": True},
                {
                    "version": "1.2.3",
                    "other": 42,
                },
            ),
            ("--update-requirements", {"update_requirements": True}, {}),
            ("--test", {"test_mode": True}, {}),
            ("--test -r", {"test_mode": True, "update_requirements": True}, {}),
            ("--", {}, {}),
            ("-- ''", {"passthrough": [""]}, {}),
            ("-- --test", {"passthrough": ["--test"]}, {}),
            ("--test -- --test", {"test_mode": True, "passthrough": ["--test"]}, {}),
            ("--test -- -r", {"test_mode": True, "passthrough": ["-r"]}, {}),
            (
                "-r -- --test",
                {"update_requirements": True, "passthrough": ["--test"]},
                {},
            ),
            ("-- -y --no maybe", {"passthrough": ["-y", "--no", "maybe"]}, {}),
            (
                "--test -- -y --no maybe",
                {"test_mode": True, "passthrough": ["-y", "--no", "maybe"]},
                {},
            ),
        ]
    ]


@pytest.mark.parametrize(
    "cmdline, expected_options, expected_overrides",
    dev_run_parameters("dev")
    + [
        ("dev --no-run", {"run_app": False}, {}),
    ],
)
def test_dev_command(
    monkeypatch,
    logger,
    console,
    cmdline,
    expected_options,
    expected_overrides,
):
    """``briefcase dev`` returns the Dev command."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    cmd, options, overrides = do_cmdline_parse(shlex.split(cmdline), logger, console)

    assert isinstance(cmd, DevCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format is None
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {
        "appname": None,
        "update_requirements": False,
        "run_app": True,
        "test_mode": False,
        "passthrough": [],
        **expected_options,
    }
    assert overrides == expected_overrides


@pytest.mark.parametrize(
    "cmdline, expected_options, expected_overrides",
    dev_run_parameters("run")
    + [
        ("run -u", {"update": True}, {}),
        ("run --update", {"update": True}, {}),
        ("run --update-resources", {"update_resources": True}, {}),
        ("run --update-support", {"update_support": True}, {}),
        ("run --no-update", {"no_update": True}, {}),
    ],
)
def test_run_command(
    monkeypatch,
    logger,
    console,
    cmdline,
    expected_options,
    expected_overrides,
):
    """``briefcase run`` returns the Run command for the correct platform."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    cmd, options, overrides = do_cmdline_parse(shlex.split(cmdline), logger, console)

    assert isinstance(cmd, macOSAppRunCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format == "app"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {
        "appname": None,
        "update": False,
        "update_requirements": False,
        "update_resources": False,
        "update_support": False,
        "no_update": False,
        "test_mode": False,
        "passthrough": [],
        **expected_options,
    }
    assert overrides == expected_overrides


@pytest.mark.parametrize(
    "cmdline,expected_options,expected_overrides",
    [
        (
            "upgrade",
            {
                "list_tools": False,
                "tool_list": [],
            },
            {},
        ),
        (
            "upgrade -C version='1.2.3' -C other=42",
            {
                "list_tools": False,
                "tool_list": [],
            },
            {
                "version": "1.2.3",
                "other": 42,
            },
        ),
    ],
)
def test_upgrade_command(
    monkeypatch,
    logger,
    console,
    cmdline,
    expected_options,
    expected_overrides,
):
    """``briefcase upgrade`` returns the upgrade command."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    cmd, options, overrides = do_cmdline_parse(cmdline.split(), logger, console)

    assert isinstance(cmd, UpgradeCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format is None
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == expected_options
    assert overrides == expected_overrides


def test_bare_command(monkeypatch, logger, console):
    """``briefcase create`` returns the macOS create app command."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    cmd, options, overrides = do_cmdline_parse("create".split(), logger, console)

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format == "app"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}
    assert overrides == {}


@pytest.mark.skipif(sys.platform != "linux", reason="requires Linux")
def test_linux_default(logger, console):
    """``briefcase create`` returns the linux create system command on Linux."""

    cmd, options, overrides = do_cmdline_parse("create".split(), logger, console)

    assert isinstance(cmd, LinuxSystemCreateCommand)
    assert cmd.platform == "linux"
    assert cmd.output_format == "system"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}


@pytest.mark.skipif(sys.platform != "darwin", reason="requires macOS")
def test_macOS_default(logger, console):
    """``briefcase create`` returns the macOS create command on Linux."""

    cmd, options, overrides = do_cmdline_parse("create".split(), logger, console)

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format == "app"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}
    assert overrides == {}


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows")
def test_windows_default(logger, console):
    """``briefcase create`` returns the Windows create app command on Windows."""

    cmd, options, overrides = do_cmdline_parse("create".split(), logger, console)

    assert isinstance(cmd, WindowsAppCreateCommand)
    assert cmd.platform == "windows"
    assert cmd.output_format == "app"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}
    assert overrides == {}


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
        "usage: briefcase create macOS app [-h] [-C KEY=VALUE] [-v] [-V] [--no-input]\n"
        "                                  [--log]\n"
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

    cmd, options, overrides = do_cmdline_parse("create linux".split(), logger, console)

    assert isinstance(cmd, LinuxSystemCreateCommand)
    assert cmd.platform == "linux"
    assert cmd.output_format == "system"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}
    assert overrides == {}


def test_command_explicit_platform_case_handling(monkeypatch, logger, console):
    """``briefcase create macOS`` returns macOS create app command."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    # This is all lower case; the command normalizes to macOS
    cmd, options, overrides = do_cmdline_parse("create macOS".split(), logger, console)

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format == "app"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}
    assert overrides == {}


def test_command_explicit_platform_help(monkeypatch, capsys, logger, console):
    """``briefcase create macOS -h`` returns the macOS create app command help."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    with pytest.raises(SystemExit) as excinfo:
        do_cmdline_parse("create macOS -h".split(), logger, console)

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Help message is for default platform and format
    output = capsys.readouterr().out
    assert output.startswith(
        "usage: briefcase create macOS app [-h] [-C KEY=VALUE] [-v] [-V] [--no-input]\n"
        "                                  [--log]\n"
        "\n"
        "Create and populate a macOS app.\n"
    )


def test_command_explicit_format(monkeypatch, logger, console):
    """``briefcase create macOS app`` returns the macOS create app command."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    cmd, options, overrides = do_cmdline_parse(
        "create macOS app".split(), logger, console
    )

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format == "app"
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}
    assert overrides == {}


def test_command_unknown_format(monkeypatch, logger, console):
    """``briefcase create macOS foobar`` returns an invalid format error."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    expected_exc_regex = r"Invalid format 'foobar'; \(choose from: app, Xcode\)"
    with pytest.raises(InvalidFormatError, match=expected_exc_regex):
        do_cmdline_parse("create macOS foobar".split(), logger, console)


def test_command_explicit_unsupported_format(monkeypatch, logger, console):
    """``briefcase create macOS homebrew`` raises an error because the format isn't
    supported (yet)"""
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
        "usage: briefcase create macOS app [-h] [-C KEY=VALUE] [-v] [-V] [--no-input]\n"
        "                                  [--log]\n"
        "\n"
        "Create and populate a macOS app.\n"
    )


def test_command_disable_input(monkeypatch, logger, console):
    """``briefcase create --no-input`` disables console input."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    cmd, options, overrides = do_cmdline_parse(
        "create --no-input".split(), logger, console
    )

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == "macOS"
    assert cmd.output_format == "app"
    assert not cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {}
    assert overrides == {}


def test_command_options(monkeypatch, capsys, logger, console):
    """Commands can provide their own arguments."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    # Invoke a command that is known to have its own custom arguments
    # (In this case, the channel argument for publication)
    cmd, options, overrides = do_cmdline_parse(
        "publish macos app -c s3".split(), logger, console
    )

    assert isinstance(cmd, macOSAppPublishCommand)
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {"channel": "s3"}
    assert overrides == {}


def test_command_overrides(monkeypatch, capsys, logger, console):
    """Configuration overrides can be specified."""
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, "platform", "darwin")

    # Invoke a command that is known to have its own custom arguments
    # (In this case, the channel argument for publication)
    cmd, options, overrides = do_cmdline_parse(
        "publish macos app -C version='1.2.3' -C extra=42".split(),
        logger,
        console,
    )

    assert isinstance(cmd, macOSAppPublishCommand)
    assert cmd.input.enabled
    assert cmd.logger.verbosity == LogLevel.INFO
    assert cmd.logger is logger
    assert cmd.input is console
    assert options == {"channel": "s3"}
    assert overrides == {
        "version": "1.2.3",
        "extra": 42,
    }


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
        "usage: briefcase publish macOS Xcode [-h] [-C KEY=VALUE] [-v] [-V]\n"
        "                                     [--no-input] [--log] [-c {s3}]\n"
        "briefcase publish macOS Xcode: error: unrecognized arguments: -x"
    )
