import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import (
    ensure_command_line_tools_are_installed
)


def test_not_installed():
    "If cmdline dev tools are not installed, raise an error."
    sub = mock.MagicMock()

    with pytest.raises(BriefcaseCommandError):
        ensure_command_line_tools_are_installed(sub=sub)

    # xcode-select was invoked
    sub.check_output.assert_called_once_with(
        ['xcode-select', '--install'],
        stderr=subprocess.STDOUT,
    )


def test_installed(capsys):
    "If cmdline dev tools *are* installed, check passes without comment."
    sub = mock.MagicMock()
    sub.check_output.side_effect = subprocess.CalledProcessError(
        cmd=['xcode-select', '--install'],
        returncode=1
    )

    # Check passes without an error...
    ensure_command_line_tools_are_installed(sub=sub)

    # ... xcode-select was invoked
    sub.check_output.assert_called_once_with(
        ['xcode-select', '--install'],
        stderr=subprocess.STDOUT,
    )

    # ...and the user is none the wiser
    out = capsys.readouterr().out
    assert len(out) == 0


def test_unsure_if_installed(capsys):
    "If xcode-select returns something odd, mention it but don't break."
    sub = mock.MagicMock()
    sub.check_output.side_effect = subprocess.CalledProcessError(
        cmd=['xcode-select', '--install'],
        returncode=69
    )

    # Check passes without an error...
    ensure_command_line_tools_are_installed(sub=sub)

    # ... xcode-select was invoked
    sub.check_output.assert_called_once_with(
        ['xcode-select', '--install'],
        stderr=subprocess.STDOUT,
    )

    # ...but stdout contains a warning
    out = capsys.readouterr().out
    assert '************' in out
