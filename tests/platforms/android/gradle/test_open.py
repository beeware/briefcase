import os
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.download import Download
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.android.gradle import GradleOpenCommand

from ....utils import create_file


def create_sdk_manager(tmp_path, extension=""):
    create_file(
        tmp_path
        / "briefcase"
        / "tools"
        / "android_sdk"
        / "cmdline-tools"
        / "latest"
        / "bin"
        / f"sdkmanager{extension}",
        "Android SDK manager",
    )


@pytest.fixture
def open_command(tmp_path, first_app_config):
    command = GradleOpenCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.os = MagicMock(spec_set=os)
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    command.tools.download = MagicMock(spec_set=Download)

    # Mock some OS calls needed to make the tools appear to exist
    command.tools.os.environ = {}
    command.tools.os.access.return_value = True

    # Mock the file marking licenses as accepted
    create_file(
        tmp_path
        / "briefcase"
        / "tools"
        / "android_sdk"
        / "licenses"
        / "android-sdk-license",
        "license accepted",
    )

    return command


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS specific test")
def test_open_macOS(open_command, first_app_config, tmp_path):
    """On macOS, open uses Finder to open the project folder."""
    # Mock the call to verify the existence of java
    open_command.tools.subprocess.check_output.return_value = "javac 1.8.0_144\n"

    # Create the project folder to mock a created project.
    open_command.project_path(first_app_config).mkdir(parents=True)

    # Create a stub sdkmanager
    create_sdk_manager(tmp_path)

    open_command(first_app_config)

    open_command.tools.subprocess.Popen.assert_called_once_with(
        ["open", tmp_path / "base_path" / "android" / "gradle" / "First App"]
    )


@pytest.mark.skipif(sys.platform != "linux", reason="Linux specific test")
def test_open_linux(open_command, first_app_config, tmp_path):
    """On linux, open invokes `xdg-open` on the project folder."""
    # Create the project folder to mock a created project.
    open_command.project_path(first_app_config).mkdir(parents=True)

    # Create a stub java binary
    create_file(tmp_path / "briefcase" / "tools" / "java" / "bin" / "java", "java")

    # Create a stub sdkmanager
    create_sdk_manager(tmp_path)

    open_command(first_app_config)

    open_command.tools.subprocess.Popen.assert_called_once_with(
        ["xdg-open", tmp_path / "base_path" / "android" / "gradle" / "First App"]
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_open_windows(open_command, first_app_config, tmp_path):
    """On Windows, open invokes `startfile` on the project folder."""
    # Create the project folder to mock a created project.
    open_command.project_path(first_app_config).mkdir(parents=True)

    # Create a stub java binary
    create_file(tmp_path / "briefcase" / "tools" / "java" / "bin" / "java", "java")

    # Create a stub sdkmanager
    create_sdk_manager(tmp_path, extension=".bat")

    open_command(first_app_config)

    open_command.tools.os.startfile.assert_called_once_with(
        tmp_path / "base_path" / "android" / "gradle" / "First App"
    )
