from unittest import mock

from briefcase.platforms.linux.flatpak import LinuxFlatpakRunCommand


def test_run(first_app_config, tmp_path):
    """A flatpak can be executed."""
    command = LinuxFlatpakRunCommand(base_path=tmp_path)
    command.flatpak = mock.MagicMock()

    command.run_app(first_app_config)

    # App is executed
    command.flatpak.run.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
    )
