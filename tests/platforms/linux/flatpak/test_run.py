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

    command.run_app(first_app_config, test_mode=False)

    # App is executed
    command.tools.flatpak.run.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
    )


def test_run_ctrl_c(first_app_config, tmp_path, capsys):
    """When CTRL-C is sent while the App is running, Briefcase exits
    normally."""
    command = LinuxFlatpakRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.flatpak = mock.MagicMock(spec_set=Flatpak)
    command.tools.flatpak.run.side_effect = KeyboardInterrupt

    # Invoke run_app (and KeyboardInterrupt does not surface)
    command.run_app(first_app_config, test_mode=False)

    # App is executed
    command.tools.flatpak.run.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
    )

    # Shows the try block for KeyboardInterrupt was entered
    assert capsys.readouterr().out.endswith(
        "[first-app] Starting app...\n"
        "===========================================================================\n"
    )
