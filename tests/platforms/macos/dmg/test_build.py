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
    first_app_config.installer_icon = 'resources/installer_icon.icns'

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


def test_installer_multi_icon(first_app_config, tmp_path):
    "If a macOS App specifies a multi-icon for the installer, it is ignored"
    # Set up an installer icon.
    first_app_config.installer_icon = {
        100: 'resources/installer_icon.100.icns',
        200: 'resources/installer_icon.200.icns',
    }

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


def test_installer_non_icns_icon(first_app_config, tmp_path):
    "If a macOS App specifies a non-icns icon for the installer, it is ignored"
    # Set up an installer icon.
    first_app_config.installer_icon = 'resources/installer_icon.png'

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
    first_app_config.installer_icon = 'resources/icon.icns'

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


def test_app_multi_icon(first_app_config, tmp_path):
    "If a macOS App specifies a multi-icon for the app, it is ignored as an installer icon candidate"
    # Set up an app icon.
    first_app_config.icon = {
        100: 'resources/icon.100.icns',
        200: 'resources/icon.200.icns',
    }

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


def test_app_non_icns_icon(first_app_config, tmp_path):
    "If a macOS App specifies a non-icns icon for the app, it is ignored as an installer icon candidate"
    # Set up an app icon.
    first_app_config.icon = 'resources/icon.png'

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
    first_app_config.installer_background = 'resources/background.png'

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
