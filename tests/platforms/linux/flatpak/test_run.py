from unittest import mock

from briefcase.console import Console, Log
from briefcase.integrations.flatpak import Flatpak
from briefcase.platforms.linux.flatpak import LinuxFlatpakRunCommand


def test_run(first_app_config, tmp_path):
    """A flatpak can be executed."""
    command = LinuxFlatpakRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.flatpak = mock.MagicMock(spec_set=Flatpak)

    command.run_app(first_app_config)

    # App is executed
    command.tools.flatpak.run.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
    )
