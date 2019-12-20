import sys
from unittest import mock

import pytest

from briefcase.platforms.macOS.dmg import macOSDmgBuildCommand

if sys.platform != 'darwin':
    pytest.skip("requires macOS", allow_module_level=True)


def test_build_dmg(first_app_config, tmp_path):
    "A macOS App can be packaged as a DMG"
    command = macOSDmgBuildCommand(base_path=tmp_path)
    command.dmgbuild = mock.MagicMock()

    command.build_app(first_app_config)

    command.dmgbuild.build_dmg.assert_called_with(
        filename=tmp_path / 'macOS' / 'First App-0.0.1.dmg',
        volume_name='First App 0.0.1',
        settings={
            'files': [str(tmp_path / 'macOS' / 'First App.app')],
            'symlinks': {'Applications': '/Applications'},
            'icon_locations': {
                'First App.app': (100, 100),
                'Applications': (300, 100),
            },
        }
    )


def test_installer_icon(first_app_config, tmp_path):
    "A macOS App can specify an icon for the installer"
    # Set up an installer icon.
    first_app_config.installer_icon = 'resources/installer_icon'
    (tmp_path / 'resources').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'resources' / 'installer_icon.icns').open('w') as f:
        f.write('icon')

    command = macOSDmgBuildCommand(base_path=tmp_path)
    command.dmgbuild = mock.MagicMock()

    command.build_app(first_app_config)

    command.dmgbuild.build_dmg.assert_called_with(
        filename=tmp_path / 'macOS' / 'First App-0.0.1.dmg',
        volume_name='First App 0.0.1',
        settings={
            'files': [str(tmp_path / 'macOS' / 'First App.app')],
            'symlinks': {'Applications': '/Applications'},
            'icon_locations': {
                'First App.app': (100, 100),
                'Applications': (300, 100),
            },
            'icon': tmp_path / 'resources' / 'installer_icon.icns'
        }
    )


def test_installer_icon_missing(first_app_config, tmp_path):
    "If the installer icon doesn't exist, it is ignored"
    # Configure an installer icon.
    first_app_config.installer_icon = 'resources/installer_icon'

    command = macOSDmgBuildCommand(base_path=tmp_path)
    command.dmgbuild = mock.MagicMock()

    command.build_app(first_app_config)

    command.dmgbuild.build_dmg.assert_called_with(
        filename=tmp_path / 'macOS' / 'First App-0.0.1.dmg',
        volume_name='First App 0.0.1',
        settings={
            'files': [str(tmp_path / 'macOS' / 'First App.app')],
            'symlinks': {'Applications': '/Applications'},
            'icon_locations': {
                'First App.app': (100, 100),
                'Applications': (300, 100),
            },
        }
    )


def test_app_icon(first_app_config, tmp_path):
    "If a macOS App doesn't specify an installer icon, the app icon will be used."
    # Set up an app icon.
    first_app_config.icon = 'resources/icon'
    (tmp_path / 'resources').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'resources' / 'icon.icns').open('w') as f:
        f.write('icon')

    command = macOSDmgBuildCommand(base_path=tmp_path)
    command.dmgbuild = mock.MagicMock()

    command.build_app(first_app_config)

    command.dmgbuild.build_dmg.assert_called_with(
        filename=tmp_path / 'macOS' / 'First App-0.0.1.dmg',
        volume_name='First App 0.0.1',
        settings={
            'files': [str(tmp_path / 'macOS' / 'First App.app')],
            'symlinks': {'Applications': '/Applications'},
            'icon_locations': {
                'First App.app': (100, 100),
                'Applications': (300, 100),
            },
            'icon': tmp_path / 'resources' / 'icon.icns'
        }
    )


def test_app_icon_missing(first_app_config, tmp_path):
    "If the app icon is missing, it is ignored as an installer icon."
    # Configure an app icon.
    first_app_config.icon = 'resources/icon'

    command = macOSDmgBuildCommand(base_path=tmp_path)
    command.dmgbuild = mock.MagicMock()

    command.build_app(first_app_config)

    command.dmgbuild.build_dmg.assert_called_with(
        filename=tmp_path / 'macOS' / 'First App-0.0.1.dmg',
        volume_name='First App 0.0.1',
        settings={
            'files': [str(tmp_path / 'macOS' / 'First App.app')],
            'symlinks': {'Applications': '/Applications'},
            'icon_locations': {
                'First App.app': (100, 100),
                'Applications': (300, 100),
            },
        }
    )


def test_build_with_background(first_app_config, tmp_path):
    "A macOS app can specify a background image for the installer."
    # Set up a background image for the installer
    first_app_config.installer_background = 'resources/background'
    (tmp_path / 'resources').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'resources' / 'background.png').open('w') as f:
        f.write('image')

    command = macOSDmgBuildCommand(base_path=tmp_path)
    command.dmgbuild = mock.MagicMock()

    command.build_app(first_app_config)

    command.dmgbuild.build_dmg.assert_called_with(
        filename=tmp_path / 'macOS' / 'First App-0.0.1.dmg',
        volume_name='First App 0.0.1',
        settings={
            'files': [str(tmp_path / 'macOS' / 'First App.app')],
            'symlinks': {'Applications': '/Applications'},
            'icon_locations': {
                'First App.app': (100, 100),
                'Applications': (300, 100),
            },
            'background': tmp_path / 'resources' / 'background.png'
        }
    )


def test_build_with_background_missing(first_app_config, tmp_path):
    "If the installer image is missing, it is ignored."
    # Configure a background image for the installer
    first_app_config.installer_background = 'resources/background'

    command = macOSDmgBuildCommand(base_path=tmp_path)
    command.dmgbuild = mock.MagicMock()

    command.build_app(first_app_config)

    command.dmgbuild.build_dmg.assert_called_with(
        filename=tmp_path / 'macOS' / 'First App-0.0.1.dmg',
        volume_name='First App 0.0.1',
        settings={
            'files': [str(tmp_path / 'macOS' / 'First App.app')],
            'symlinks': {'Applications': '/Applications'},
            'icon_locations': {
                'First App.app': (100, 100),
                'Applications': (300, 100),
            },
        }
    )
