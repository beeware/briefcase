import subprocess
from pathlib import Path
from unittest import mock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux.appimage import LinuxAppImageBuildCommand


@pytest.fixture
def build_command(tmp_path, first_app_config):
    command = LinuxAppImageBuildCommand(
        base_path=tmp_path,
        # `dot-briefcase` below makes it easy to find references to literal
        # `.briefcase` when grepping the source.
        dot_briefcase_path=tmp_path / "dot-briefcase",
        apps={'first': first_app_config}
    )
    command.host_os = 'Linux'
    command.host_arch = 'wonky'

    command.os = mock.MagicMock()
    command.os.environ.copy.return_value = {
        'PATH': '/usr/local/bin:/usr/bin'
    }

    command.subprocess = mock.MagicMock()

    command.linuxdeploy_appimage = tmp_path / 'tools' / 'linuxdeploy-wonky.AppImage'
    return command


def test_linuxdeploy_download_url(build_command):
    assert (
        build_command.linuxdeploy_download_url
        == 'https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-wonky.AppImage'
    )


def test_verify_tools(build_command, first_app_config, tmp_path):
    "The build process invokes verify_tools, which retrieves linuxdeploy"

    build_command.build_app = mock.MagicMock()
    build_command.download_url = mock.MagicMock(return_value='new-downloaded-file')

    # Make it look like the template has been generated
    (tmp_path / 'linux' / 'First App').mkdir(parents=True, exist_ok=True)

    # Invoke the full build.
    build_command()

    # The downloaded file will be made executable
    build_command.os.chmod.assert_called_with('new-downloaded-file', 0o755)

    # The build command retains the path to the downloaded file.
    assert build_command.linuxdeploy_appimage == 'new-downloaded-file'

    # build_app will be invoked on the apps.
    build_command.build_app.assert_called_with(first_app_config)


def test_verify_tools_wrong_platform(build_command):
    "If we're not on Linux, the build fails"

    build_command.host_os = 'TestOS'
    build_command.build_app = mock.MagicMock()
    build_command.download_url = mock.MagicMock()

    # Try to invoke the build
    with pytest.raises(BriefcaseCommandError):
        build_command()

    # The download was not attempted
    assert build_command.download_url.call_count == 0

    # But it failed, so the file won't be made executable...
    assert build_command.os.chmod.call_count == 0

    # and the command won't retain the downloaded filename.
    assert build_command.linuxdeploy_appimage != 'new-downloaded-file'

    # and no build will be attempted
    assert build_command.build_app.call_count == 0


def test_verify_tools_download_failure(build_command):
    "If the build tools can't be retrieved, the build fails"
    build_command.build_app = mock.MagicMock()
    build_command.download_url = mock.MagicMock(
        side_effect=requests_exceptions.ConnectionError
    )

    # Try to invoke the build
    with pytest.raises(BriefcaseCommandError):
        build_command()

    # The download was attempted
    build_command.download_url.assert_called_with(
        url='https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-wonky.AppImage',
        download_path=build_command.dot_briefcase_path / 'tools'
    )

    # But it failed, so the file won't be made executable...
    assert build_command.os.chmod.call_count == 0

    # and the command won't retain the downloaded filename.
    assert build_command.linuxdeploy_appimage != 'new-downloaded-file'

    # and no build will be attempted
    assert build_command.build_app.call_count == 0


def test_build_appimage(build_command, first_app_config, tmp_path):
    "A Linux app can be packaged as an AppImage"

    build_command.build_app(first_app_config)

    # linuxdeploy was invoked
    app_dir = tmp_path / 'linux' / 'First App' / 'First App.AppDir'
    build_command.subprocess.run.assert_called_with(
        [
            str(build_command.linuxdeploy_appimage),
            "--appdir={appdir}".format(appdir=app_dir),
            "-d", str(app_dir / "com.example.first-app.desktop"),
            "-o", "appimage",
        ],
        env={
            'PATH': '/usr/local/bin:/usr/bin',
            'VERSION': '0.0.1',
        },
        check=True,
        cwd=str(tmp_path / 'linux')
    )
    # Binary is marked executable
    build_command.os.chmod.assert_called_with(
        str(tmp_path / 'linux' / 'First_App-0.0.1-wonky.AppImage'),
        0o755
    )


def test_build_failure(build_command, first_app_config, tmp_path):
    "If linuxdeploy fails, the build is stopped."

    # Mock a failure in the build
    build_command.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=['linuxdeploy-x86_64.AppImage', '...'],
        returncode=1
    )

    # Invoking the build will raise an error.
    with pytest.raises(BriefcaseCommandError):
        build_command.build_app(first_app_config)

    # linuxdeploy was invoked
    app_dir = tmp_path / 'linux' / 'First App' / 'First App.AppDir'
    build_command.subprocess.run.assert_called_with(
        [
            str(build_command.linuxdeploy_appimage),
            "--appdir={appdir}".format(appdir=app_dir),
            "-d", str(app_dir / "com.example.first-app.desktop"),
            "-o", "appimage",
        ],
        env={
            'PATH': '/usr/local/bin:/usr/bin',
            'VERSION': '0.0.1',
        },
        check=True,
        cwd=str(tmp_path / 'linux')
    )

    # chmod isn't invoked if the binary wasn't created.
    assert build_command.os.chmod.call_count == 0
