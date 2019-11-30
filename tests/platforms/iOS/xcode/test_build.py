import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.iOS.xcode import iOSXcodeBuildCommand


def test_build_app(first_app_config, tmp_path):
    "An iOS App can be built"
    command = iOSXcodeBuildCommand(base_path=tmp_path)

    # A valid target device will be selected.
    command.select_target_device = mock.MagicMock(
        return_value=(
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', '13.2', 'iPhone 11'
        )
    )
    command.subprocess = mock.MagicMock()

    command.build_app(first_app_config)

    command.subprocess.run.assert_called_with(
        [
            'xcodebuild',
            '-project', tmp_path / 'iOS' / 'First App' / 'First App.xcodeproj',
            '-destination',
            'platform="iOS Simulator,name=iPhone 11,OS=13.2"',
            '-quiet',
            '-configuration', 'Debug',
            '-arch', 'x86_64',
            '-sdk', 'iphonesimulator',
            'build'
        ],
        check=True
    )


def test_build_app_failed(first_app_config, tmp_path):
    "If xcodebuild fails, an error is raised."
    command = iOSXcodeBuildCommand(base_path=tmp_path)

    # A valid target device will be selected.
    command.select_target_device = mock.MagicMock(
        return_value=(
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', '13.2', 'iPhone 11'
        )
    )
    # The subprocess.run() call will raise an error
    command.subprocess = mock.MagicMock()
    command.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=['xcodebuild', '...'],
        returncode=1
    )

    with pytest.raises(BriefcaseCommandError):
        command.build_app(first_app_config)

    command.subprocess.run.assert_called_with(
        [
            'xcodebuild',
            '-project', tmp_path / 'iOS' / 'First App' / 'First App.xcodeproj',
            '-destination',
            'platform="iOS Simulator,name=iPhone 11,OS=13.2"',
            '-quiet',
            '-configuration', 'Debug',
            '-arch', 'x86_64',
            '-sdk', 'iphonesimulator',
            'build'
        ],
        check=True
    )
