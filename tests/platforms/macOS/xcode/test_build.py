import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS.xcode import macOSXcodeBuildCommand


def test_build_app(first_app_config, tmp_path):
    "An macOS App can be built"
    command = macOSXcodeBuildCommand(base_path=tmp_path)

    command.subprocess = mock.MagicMock()
    command.build_app(first_app_config)

    command.subprocess.run.assert_called_with(
        [
            'xcodebuild',
            '-project', tmp_path / 'macOS' / 'Xcode' / 'First App' / 'First App.xcodeproj',
            '-quiet',
            '-configuration', 'Release',
            'build'
        ],
        check=True
    )


def test_build_app_failed(first_app_config, tmp_path):
    "If xcodebuild fails, an error is raised."
    command = macOSXcodeBuildCommand(base_path=tmp_path)

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
            '-project', tmp_path / 'macOS' / 'Xcode' / 'First App' / 'First App.xcodeproj',
            '-quiet',
            '-configuration', 'Release',
            'build'
        ],
        check=True
    )
