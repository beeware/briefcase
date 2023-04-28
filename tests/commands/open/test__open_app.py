import sys
from unittest.mock import MagicMock

import pytest


def test_open_macOS(open_command, tmp_path):
    """On macOS, open invokes `open`"""
    open_command.tools.host_os = "Darwin"

    open_command(app=open_command.apps["first"])

    open_command.tools.subprocess.Popen.assert_called_once_with(
        [
            "open",
            tmp_path
            / "base_path"
            / "build"
            / "first"
            / "tester"
            / "dummy"
            / "first.project",
        ]
    )


def test_open_linux(open_command, tmp_path):
    """On linux, open invokes `xdg-open`"""
    open_command.tools.host_os = "Linux"

    open_command(app=open_command.apps["first"])

    open_command.tools.subprocess.Popen.assert_called_once_with(
        [
            "xdg-open",
            tmp_path
            / "base_path"
            / "build"
            / "first"
            / "tester"
            / "dummy"
            / "first.project",
        ]
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_open_windows(open_command, tmp_path):
    """On Windows, open invokes `startfile`"""

    open_command(app=open_command.apps["first"])

    open_command.tools.os.startfile.assert_called_once_with(
        tmp_path
        / "base_path"
        / "build"
        / "first"
        / "tester"
        / "dummy"
        / "first.project"
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Windows specific test")
def test_open_windows_on_nonwindows(open_command, tmp_path):
    """When the host is non-Windows but mocking Windows, open invokes `startfile`"""
    open_command.tools.host_os = "Windows"
    # cannot use `spec_set=os` since os.startfile is only on Windows
    open_command.tools.os = MagicMock()

    open_command(app=open_command.apps["first"])

    open_command.tools.os.startfile.assert_called_once_with(
        tmp_path
        / "base_path"
        / "build"
        / "first"
        / "tester"
        / "dummy"
        / "first.project"
    )
