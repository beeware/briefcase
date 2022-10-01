import os
from subprocess import CalledProcessError
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.windows.app import WindowsAppRunCommand


def test_run_app(first_app_config, tmp_path):
    """A Windows app can be started."""
    command = WindowsAppRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    command.run_app(first_app_config)

    command.tools.subprocess.run.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "windows"
                / "app"
                / "First App"
                / "src"
                / "First App.exe"
            ),
        ],
        cwd=tmp_path / "home",
        check=True,
        stream_output=True,
    )


def test_run_app_failed(first_app_config, tmp_path):
    """If there's a problem started the app, an exception is raised."""
    command = WindowsAppRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command.tools.subprocess.run.side_effect = CalledProcessError(
        cmd=["First App.exe"], returncode=1
    )

    with pytest.raises(BriefcaseCommandError, match=r"Unable to start app first-app."):
        command.run_app(first_app_config)

    # The run command was still invoked, though
    command.tools.subprocess.run.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "windows"
                / "app"
                / "First App"
                / "src"
                / "First App.exe"
            ),
        ],
        cwd=tmp_path / "home",
        check=True,
        stream_output=True,
    )
