import sys

import pytest

from briefcase import __version__
from briefcase.cmdline import parse_cmdline
from briefcase.exceptions import (
    InvalidFormatError,
    NoCommandError,
    ShowOutputFormats,
    UnsupportedCommandError,
)
from briefcase.platforms.macos.app import (
    MacOSAppCreateCommand,
    MacOSAppPublishCommand,
)
from briefcase.platforms.macos.dmg import MacOSDmgCreateCommand
from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand
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


def test_bare_command(monkeypatch):
    "``briefcase create`` returns the macOS create app command"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    cmd = parse_cmdline('create'.split())

    assert isinstance(cmd, MacOSAppCreateCommand)


@pytest.mark.skipif(sys.platform != 'linux', reason="requires Linux")
def test_linux_default():
    "``briefcase create`` returns the linux create appimage command on Linux"

    cmd = parse_cmdline('create'.split())

    assert isinstance(cmd, LinuxAppImageCreateCommand)


@pytest.mark.skipif(sys.platform != 'darwin', reason="requires macOS")
def test_macOS_default():
    "``briefcase create`` returns the linux create appimage command on Linux"

    cmd = parse_cmdline('create'.split())

    assert isinstance(cmd, MacOSAppCreateCommand)


@pytest.mark.skipif(sys.platform != 'win32', reason="requires Windows")
def test_windows_default():
    "``briefcase create`` returns the Windows create msi command on Windows"

    cmd = parse_cmdline('create'.split())

    assert isinstance(cmd, WindowsMSICreateCommand)


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
        "usage: briefcase create macos app [-h] [-v] [-V]\n"
        "\n"
        "Create and populate a macOS .app bundle.\n"
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

    assert excinfo.value.platform == 'macos'
    assert excinfo.value.default == 'app'
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

    cmd = parse_cmdline('create linux'.split())

    assert isinstance(cmd, LinuxAppImageCreateCommand)


def test_command_explicit_platform_case_handling(monkeypatch):
    "``briefcase create macOS`` returns macOs create app command"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    # This is all lower case; the command normalizes to macos
    cmd = parse_cmdline('create macOS'.split())

    assert isinstance(cmd, MacOSAppCreateCommand)


def test_command_explicit_platform_help(monkeypatch, capsys):
    "``briefcase create macos -h`` returns the macOS create app command help"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(SystemExit) as excinfo:
        parse_cmdline('create macos -h'.split())

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Help message is for default platform and format
    output = capsys.readouterr().out
    assert output.startswith(
        "usage: briefcase create macos app [-h] [-v] [-V]\n"
        "\n"
        "Create and populate a macOS .app bundle.\n"
        "\n"
        "optional arguments:"
    )


def test_command_explicit_platform_show_formats(monkeypatch):
    "``briefcase create macos -f`` shows formats for the platform"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(ShowOutputFormats) as excinfo:
        parse_cmdline('create macos -f'.split())

    assert excinfo.value.platform == 'macos'
    assert excinfo.value.default == 'app'
    assert set(excinfo.value.choices) == {'app', 'dmg', 'homebrew'}


def test_command_explicit_format(monkeypatch):
    "``briefcase create macos dmg`` returns the macOS create dmg command"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    cmd = parse_cmdline('create macos dmg'.split())

    assert isinstance(cmd, MacOSDmgCreateCommand)


def test_command_unknown_format(monkeypatch):
    "``briefcase create macos foobar`` returns an invalid format error"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(InvalidFormatError):
        parse_cmdline('create macos foobar'.split())


def test_command_explicit_unsupported_format(monkeypatch):
    "``briefcase create wearos apk`` raises an error because the platform isn't supported yet"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(UnsupportedCommandError):
        parse_cmdline('create wearos apk'.split())


def test_command_explicit_format_help(monkeypatch, capsys):
    "``briefcase create macos dmg -h`` returns the macOS create dmg help"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(SystemExit) as excinfo:
        parse_cmdline('create macos dmg -h'.split())

    # Normal exit due to displaying help
    assert excinfo.value.code == 0
    # Help message is for default platform, but dmg format
    output = capsys.readouterr().out
    assert output.startswith(
        "usage: briefcase create macos dmg [-h] [-v] [-V]\n"
        "\n"
        "Create and populate a macOS .dmg bundle.\n"
        "\n"
        "optional arguments:"
    )


def test_command_explicit_format_show_formats(monkeypatch):
    "``briefcase create macos dmg -f`` shows formats for the platform"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    with pytest.raises(ShowOutputFormats) as excinfo:
        parse_cmdline('create macos dmg -f'.split())

    assert excinfo.value.platform == 'macos'
    assert excinfo.value.default == 'app'
    assert set(excinfo.value.choices) == {'app', 'dmg', 'homebrew'}


def test_command_options(monkeypatch, capsys):
    "Commands can provide their own arguments"
    # Pretend we're on macOS, regardless of where the tests run.
    monkeypatch.setattr(sys, 'platform', 'darwin')

    # Invoke a command that is known to have it's own custom arguments
    # (In this case, the channel argument for publication)
    cmd = parse_cmdline('publish macos app -c s3'.split())

    assert isinstance(cmd, MacOSAppPublishCommand)
    assert cmd.options.channel == 's3'
