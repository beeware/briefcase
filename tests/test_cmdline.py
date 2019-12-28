import sys

import pytest

from briefcase import __version__
from briefcase.cmdline import parse_cmdline
from briefcase.commands import DevCommand, NewCommand
from briefcase.exceptions import (
    InvalidFormatError,
    NoCommandError,
    ShowOutputFormats,
    UnsupportedCommandError
)
from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand
from briefcase.platforms.macOS.app import (
    macOSAppCreateCommand,
    macOSAppPublishCommand
)
from briefcase.platforms.macOS.dmg import macOSDmgCreateCommand
from briefcase.platforms.windows.msi import WindowsMSICreateCommand


def test_empty():
    "``briefcase`` returns basic usage"
    with pytest.raises(NoCommandError) as excinfo:
        parse_cmdline(''.split())

    assert excinfo.value.msg.startswith(
        'usage: briefcase [-h] <command> [<platform>] [<format>] ...\n'
        '\n'
        'Package Python code for distribution.\n'
        '\n'
        'positional arguments:\n'
    )


def test_help_only():
    "``briefcase -h`` returns basic usage"
    with pytest.raises(NoCommandError) as excinfo:
        parse_cmdline('-h'.split())

    assert excinfo.value.msg.startswith(
        'usage: briefcase [-h] <command> [<platform>] [<format>] ...\n'
        '\n'
        'Package Python code for distribution.\n'
        '\n'
        'positional arguments:\n'
    )


def test_version_only(capsys):
    "``briefcase -V`` returns current version"
    with pytest.raises(SystemExit) as excinfo:
        parse_cmdline('-V'.split())

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Version is displayed.
    output = capsys.readouterr().out
    assert output == '{__version__}\n'.format(__version__=__version__)


def test_show_output_formats_only():
    "``briefcase -f`` returns basic usage as a command is needed"
    with pytest.raises(NoCommandError) as excinfo:
        parse_cmdline('-f'.split())

    assert excinfo.value.msg.startswith(
        'usage: briefcase [-h] <command> [<platform>] [<format>] ...\n'
        '\n'
        'Package Python code for distribution.\n'
        '\n'
        'positional arguments:\n'
    )


def test_unknown_command():
    "``briefcase foobar`` fails as an invalid command"
    with pytest.raises(SystemExit) as excinfo:
        parse_cmdline('foobar'.split())

    assert excinfo.value.code == 2
    assert excinfo.value.__context__.argument_name == 'command'
    assert excinfo.value.__context__.message.startswith("invalid choice: 'foobar' (choose from")


def test_new_command():
    "``briefcase new`` returns the New command"
    cmd, options = parse_cmdline('new'.split())

    assert isinstance(cmd, NewCommand)
    assert cmd.platform == 'all'
    assert cmd.output_format is None
    assert options == {'template': None, 'verbosity': 1}


def test_dev_command(monkeypatch):
    "``briefcase dev`` returns the Dev command"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    cmd, options = parse_cmdline('dev'.split())

    assert isinstance(cmd, DevCommand)
    assert cmd.platform == 'macOS'
    assert cmd.output_format is None
    assert options == {
        'verbosity': 1,
        'appname': None,
        'update_dependencies': False
    }


def test_bare_command(monkeypatch):
    "``briefcase create`` returns the macOS create app command"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    cmd, options = parse_cmdline('create'.split())

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == 'macOS'
    assert cmd.output_format == 'dmg'
    assert options == {'verbosity': 1}


@pytest.mark.skipif(sys.platform != 'linux', reason="requires Linux")
def test_linux_default():
    "``briefcase create`` returns the linux create appimage command on Linux"

    cmd, options = parse_cmdline('create'.split())

    assert isinstance(cmd, LinuxAppImageCreateCommand)
    assert cmd.platform == 'linux'
    assert cmd.output_format == 'appimage'
    assert options == {'verbosity': 1}


@pytest.mark.skipif(sys.platform != 'darwin', reason="requires macOS")
def test_macOS_default():
    "``briefcase create`` returns the linux create appimage command on Linux"

    cmd, options = parse_cmdline('create'.split())

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == 'macOS'
    assert cmd.output_format == 'dmg'
    assert options == {'verbosity': 1}


@pytest.mark.skipif(sys.platform != 'win32', reason="requires Windows")
def test_windows_default():
    "``briefcase create`` returns the Windows create msi command on Windows"

    cmd, options = parse_cmdline('create'.split())

    assert isinstance(cmd, WindowsMSICreateCommand)
    assert cmd.platform == 'windows'
    assert cmd.output_format == 'msi'
    assert options == {'verbosity': 1}


def test_bare_command_help(monkeypatch, capsys):
    "``briefcase create -h`` returns the macOS create app command help"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(SystemExit) as excinfo:
        parse_cmdline('create -h'.split())

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Help message is for default platform and format
    output = capsys.readouterr().out
    assert output.startswith(
        "usage: briefcase create macOS dmg [-h] [-v] [-V]\n"
        "\n"
        "Create and populate a macOS app.\n"
        "\n"
        "optional arguments:"
    )


def test_bare_command_version(capsys):
    "``briefcase create -V`` returns the version"
    with pytest.raises(SystemExit) as excinfo:
        parse_cmdline('create -V'.split())

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Version is displayed.
    output = capsys.readouterr().out
    assert output == '{__version__}\n'.format(__version__=__version__)


def test_bare_command_show_formats(monkeypatch):
    "``briefcase create -f`` returns an error indicating a platform is needed"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(ShowOutputFormats) as excinfo:
        parse_cmdline('create -f'.split())

    assert excinfo.value.platform == 'macOS'
    assert excinfo.value.default == 'dmg'
    assert set(excinfo.value.choices) == {'app', 'dmg', 'homebrew'}


def test_command_unknown_platform(monkeypatch):
    "``briefcase create foobar`` raises an unknown platform error"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(SystemExit) as excinfo:
        parse_cmdline('create foobar'.split())

    assert excinfo.value.code == 2
    assert excinfo.value.__context__.argument_name == 'platform'
    assert excinfo.value.__context__.message.startswith("invalid choice: 'foobar' (choose from")


def test_command_explicit_platform(monkeypatch):
    "``briefcase create linux`` returns linux create app command"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    cmd, options = parse_cmdline('create linux'.split())

    assert isinstance(cmd, LinuxAppImageCreateCommand)
    assert cmd.platform == 'linux'
    assert cmd.output_format == 'appimage'
    assert options == {'verbosity': 1}


def test_command_explicit_platform_case_handling(monkeypatch):
    "``briefcase create macOS`` returns macOS create app command"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    # This is all lower case; the command normalizes to macOS
    cmd, options = parse_cmdline('create macOS'.split())

    assert isinstance(cmd, macOSAppCreateCommand)
    assert cmd.platform == 'macOS'
    assert cmd.output_format == 'dmg'
    assert options == {'verbosity': 1}


def test_command_explicit_platform_help(monkeypatch, capsys):
    "``briefcase create macOS -h`` returns the macOS create app command help"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(SystemExit) as excinfo:
        parse_cmdline('create macOS -h'.split())

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Help message is for default platform and format
    output = capsys.readouterr().out
    assert output.startswith(
        "usage: briefcase create macOS dmg [-h] [-v] [-V]\n"
        "\n"
        "Create and populate a macOS app.\n"
        "\n"
        "optional arguments:"
    )


def test_command_explicit_platform_show_formats(monkeypatch):
    "``briefcase create macOS -f`` shows formats for the platform"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(ShowOutputFormats) as excinfo:
        parse_cmdline('create macOS -f'.split())

    assert excinfo.value.platform == 'macOS'
    assert excinfo.value.default == 'dmg'
    assert set(excinfo.value.choices) == {'app', 'dmg', 'homebrew'}


def test_command_explicit_format(monkeypatch):
    "``briefcase create macOS dmg`` returns the macOS create dmg command"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    cmd, options = parse_cmdline('create macOS dmg'.split())

    assert isinstance(cmd, macOSDmgCreateCommand)
    assert cmd.platform == 'macOS'
    assert cmd.output_format == 'dmg'
    assert options == {'verbosity': 1}


def test_command_unknown_format(monkeypatch):
    "``briefcase create macOS foobar`` returns an invalid format error"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(InvalidFormatError):
        parse_cmdline('create macOS foobar'.split())


def test_command_explicit_unsupported_format(monkeypatch):
    "``briefcase create macOS homebrew`` raises an error because the format isn't supported (yet)"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(UnsupportedCommandError):
        parse_cmdline('create macOS homebrew'.split())


def test_command_explicit_format_help(monkeypatch, capsys):
    "``briefcase create macOS dmg -h`` returns the macOS create dmg help"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(SystemExit) as excinfo:
        parse_cmdline('create macOS dmg -h'.split())

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Help message is for default platform, but dmg format
    output = capsys.readouterr().out
    assert output.startswith(
        "usage: briefcase create macOS dmg [-h] [-v] [-V]\n"
        "\n"
        "Create and populate a macOS app.\n"
        "\n"
        "optional arguments:"
    )


def test_command_explicit_format_show_formats(monkeypatch):
    "``briefcase create macOS dmg -f`` shows formats for the platform"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(ShowOutputFormats) as excinfo:
        parse_cmdline('create macOS dmg -f'.split())

    assert excinfo.value.platform == 'macOS'
    assert excinfo.value.default == 'dmg'
    assert set(excinfo.value.choices) == {'app', 'dmg', 'homebrew'}


def test_command_options(monkeypatch, capsys):
    "Commands can provide their own arguments"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    # Invoke a command that is known to have it's own custom arguments
    # (In this case, the channel argument for publication)
    cmd, options = parse_cmdline('publish macos app -c s3'.split())

    assert isinstance(cmd, macOSAppPublishCommand)
    assert options == {
        'verbosity': 1,
        'channel': 's3'
    }


def test_unknown_command_options(monkeypatch, capsys):
    "Commands can provide their own arguments"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    # Invoke a command but provide an option. that isn't defined
    with pytest.raises(SystemExit) as excinfo:
        parse_cmdline('publish macOS app -x foobar'.split())

    # Normal exit due to displaying help
    assert excinfo.value.code == 2
    # Help message is for default platform and format
    output = capsys.readouterr().err

    assert output.startswith(
        "usage: briefcase publish macOS app [-h] [-v] [-V] [-c {s3}]\n"
        "briefcase publish macOS app: error: unrecognized arguments: -x"
    )
