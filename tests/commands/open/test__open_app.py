import sys

import pytest


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS specific test")
def test_open_macOS(open_command, tmp_path):
    """On macOS, open invokes `open`"""
    open_command(app=open_command.apps["first"])

    open_command.tools.subprocess.Popen.assert_called_once_with(
        ["open", tmp_path / "tester" / "dummy" / "first" / "first.project"]
    )


@pytest.mark.skipif(sys.platform != "linux", reason="Linux specific test")
def test_open_linux(open_command, tmp_path):
    """On linux, open invokes `xdg-open`"""
    open_command(app=open_command.apps["first"])

    open_command.tools.subprocess.Popen.assert_called_once_with(
        ["xdg-open", tmp_path / "tester" / "dummy" / "first" / "first.project"]
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_open_windows(open_command, tmp_path):
    """On Windows, open invokes `startfile`"""
    open_command(app=open_command.apps["first"])

    open_command.tools.os.startfile.assert_called_once_with(
        tmp_path / "tester" / "dummy" / "first" / "first.project"
    )
