import platform

import pytest


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS specific test")
def test_open_macOS(open_command, tmp_path):
    """On macOS, open invokes `open`"""
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


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux specific test")
def test_open_linux(open_command, tmp_path):
    """On linux, open invokes `xdg-open`"""
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


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows specific test")
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
