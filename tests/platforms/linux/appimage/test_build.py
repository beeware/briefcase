import os
import subprocess
import sys
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError, NetworkFailure
from briefcase.integrations.docker import DockerAppContext
from briefcase.integrations.linuxdeploy import LinuxDeploy
from briefcase.platforms.linux.appimage import LinuxAppImageBuildCommand


@pytest.fixture
def first_app(first_app_config, tmp_path):
    """A fixture for the first app, rolled out on disk."""
    # Make it look like the template has been generated
    app_dir = (
        tmp_path / "base_path" / "linux" / "appimage" / "First App" / "First App.AppDir"
    )
    (app_dir / "usr" / "app" / "support").mkdir(parents=True, exist_ok=True)
    (app_dir / "usr" / "app_packages" / "firstlib").mkdir(parents=True, exist_ok=True)
    (app_dir / "usr" / "app_packages" / "secondlib").mkdir(parents=True, exist_ok=True)

    # Create some .so files
    (app_dir / "usr" / "app" / "support" / "support.so").touch()
    (app_dir / "usr" / "app_packages" / "firstlib" / "first.so").touch()
    (app_dir / "usr" / "app_packages" / "secondlib" / "second_a.so").touch()
    (app_dir / "usr" / "app_packages" / "secondlib" / "second_b.so").touch()

    return first_app_config


@pytest.fixture
def build_command(tmp_path, first_app_config):
    command = LinuxAppImageBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
        apps={"first": first_app_config},
    )
    command.tools.host_os = "Linux"
    command.tools.host_arch = "wonky"
    command.use_docker = False
    command._path_index = {
        first_app_config: {
            "app_path": "First App.AppDir/usr/app",
            "app_packages_path": "First App.AppDir/usr/app_packages",
        }
    }

    # Reset `os` mock without `spec` so tests can run on Windows where os.getuid doesn't exist.
    command.tools.os = mock.MagicMock()
    # Mock user and group IDs for docker image
    command.tools.os.environ = mock.MagicMock()
    command.tools.os.environ.__getitem__.return_value = (
        "/usr/local/bin:/usr/bin:/path/to/somewhere"
    )
    command.tools.os.environ.copy.return_value = {
        "PATH": "/usr/local/bin:/usr/bin:/path/to/somewhere"
    }

    # mock user and group IDs for docker build
    command.tools.os.getuid.return_value = 1000
    command.tools.os.getgid.return_value = 1001

    # Store the underlying subprocess instance
    command._subprocess = mock.MagicMock(spec_set=subprocess)
    command.tools.subprocess._subprocess = command._subprocess

    # mock `echo $PATH` check_output call
    command.tools.subprocess._subprocess.check_output.return_value = (
        "/usr/local/bin:/usr/bin:/path/to/somewhere"
    )

    # Short circuit the process streamer
    wait_bar_streamer = mock.MagicMock()
    wait_bar_streamer.stdout.readline.return_value = ""
    wait_bar_streamer.poll.return_value = 0
    command.tools.subprocess._subprocess.Popen.return_value.__enter__.return_value = (
        wait_bar_streamer
    )

    command.tools.linuxdeploy = LinuxDeploy(command.tools)
    return command


def test_verify_tools_wrong_platform(build_command):
    """If we're not on Linux, the build fails."""

    build_command.tools.host_os = "TestOS"
    build_command.build_app = mock.MagicMock()
    build_command.tools.download.file = mock.MagicMock()

    # Try to invoke the build
    with pytest.raises(BriefcaseCommandError):
        build_command()

    # The download was not attempted
    assert build_command.tools.download.file.call_count == 0

    # But it failed, so the file won't be made executable...
    assert build_command.tools.os.chmod.call_count == 0

    # and no build will be attempted
    assert build_command.build_app.call_count == 0


def test_verify_tools_download_failure(build_command):
    """If the build tools can't be retrieved, the build fails."""
    # Remove linuxdeploy tool so download is attempted
    delattr(build_command.tools, "linuxdeploy")

    build_command.build_app = mock.MagicMock()
    build_command.tools.download.file = mock.MagicMock(
        side_effect=NetworkFailure("mock")
    )

    # Try to invoke the build
    with pytest.raises(BriefcaseCommandError):
        build_command()

    # The download was attempted
    build_command.tools.download.file.assert_called_with(
        url="https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-wonky.AppImage",
        download_path=build_command.tools.base_path,
        role="linuxdeploy",
    )

    # But it failed, so the file won't be made executable...
    assert build_command.tools.os.chmod.call_count == 0

    # and no build will be attempted
    assert build_command.build_app.call_count == 0


def test_build_appimage(build_command, first_app, tmp_path):
    """A Linux app can be packaged as an AppImage."""

    build_command.verify_app_tools(first_app)
    build_command.build_app(first_app)

    # linuxdeploy was invoked
    app_dir = (
        tmp_path / "base_path" / "linux" / "appimage" / "First App" / "First App.AppDir"
    )
    build_command._subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path / "briefcase" / "tools" / "linuxdeploy-wonky.AppImage"
            ),
            "--appdir",
            os.fsdecode(app_dir),
            "--desktop-file",
            os.fsdecode(app_dir / "com.example.first-app.desktop"),
            "--output",
            "appimage",
            "--deploy-deps-only",
            os.fsdecode(app_dir / "usr" / "app" / "support"),
            "--deploy-deps-only",
            os.fsdecode(app_dir / "usr" / "app_packages" / "firstlib"),
            "--deploy-deps-only",
            os.fsdecode(app_dir / "usr" / "app_packages" / "secondlib"),
        ],
        env={
            "PATH": "/usr/local/bin:/usr/bin:/path/to/somewhere",
            "VERSION": "0.0.1",
            "DISABLE_COPYRIGHT_FILES_DEPLOYMENT": "1",
            "APPIMAGE_EXTRACT_AND_RUN": "1",
            "ARCH": "wonky",
        },
        cwd=os.fsdecode(tmp_path / "base_path" / "linux"),
        text=True,
        encoding=mock.ANY,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    # Binary is marked executable
    build_command.tools.os.chmod.assert_called_with(
        tmp_path / "base_path" / "linux" / "First_App-0.0.1-wonky.AppImage", 0o755
    )


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows paths can't be passed to linuxdeploy",
)
def test_build_appimage_with_plugin(build_command, first_app, tmp_path):
    """A Linux app can be packaged as an AppImage with a plugin."""
    # Mock the existence of some plugins
    gtk_plugin_path = (
        tmp_path
        / "briefcase"
        / "tools"
        / "linuxdeploy_plugins"
        / "gtk"
        / "linuxdeploy-plugin-gtk.sh"
    )
    gtk_plugin_path.parent.mkdir(parents=True)
    gtk_plugin_path.touch()

    local_file_plugin_path = tmp_path / "local" / "linuxdeploy-plugin-something.sh"
    local_file_plugin_path.parent.mkdir(parents=True)
    local_file_plugin_path.touch()

    # Configure the app to use the plugins
    first_app.linuxdeploy_plugins = [
        "DEPLOY_GTK_VERSION=3 gtk",
        os.fsdecode(local_file_plugin_path),
    ]

    # Build the app
    build_command.verify_app_tools(first_app)
    build_command.build_app(first_app)

    # linuxdeploy was invoked
    app_dir = (
        tmp_path / "base_path" / "linux" / "appimage" / "First App" / "First App.AppDir"
    )
    build_command._subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path / "briefcase" / "tools" / "linuxdeploy-wonky.AppImage"
            ),
            "--appdir",
            os.fsdecode(app_dir),
            "--desktop-file",
            os.fsdecode(app_dir / "com.example.first-app.desktop"),
            "--output",
            "appimage",
            "--deploy-deps-only",
            os.fsdecode(app_dir / "usr" / "app" / "support"),
            "--deploy-deps-only",
            os.fsdecode(app_dir / "usr" / "app_packages" / "firstlib"),
            "--deploy-deps-only",
            os.fsdecode(app_dir / "usr" / "app_packages" / "secondlib"),
            "--plugin",
            "gtk",
            "--plugin",
            "something",
        ],
        env={
            "PATH": f"{gtk_plugin_path.parent}:{app_dir.parent}:/usr/local/bin:/usr/bin:/path/to/somewhere",
            "DEPLOY_GTK_VERSION": "3",
            "VERSION": "0.0.1",
            "DISABLE_COPYRIGHT_FILES_DEPLOYMENT": "1",
            "APPIMAGE_EXTRACT_AND_RUN": "1",
            "ARCH": "wonky",
        },
        cwd=os.fsdecode(tmp_path / "base_path" / "linux"),
        text=True,
        encoding=mock.ANY,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    # Local plugin marked executable
    build_command.tools.os.chmod.assert_any_call(
        tmp_path
        / "base_path"
        / "linux"
        / "appimage"
        / "First App"
        / "linuxdeploy-plugin-something.sh",
        0o755,
    )
    # Binary is marked executable
    build_command.tools.os.chmod.assert_called_with(
        tmp_path / "base_path" / "linux" / "First_App-0.0.1-wonky.AppImage", 0o755
    )


def test_build_failure(build_command, first_app, tmp_path):
    """If linuxdeploy fails, the build is stopped."""
    # Mock a failure in the build
    build_command._subprocess.Popen.side_effect = subprocess.CalledProcessError(
        cmd=["linuxdeploy-x86_64.AppImage", "..."],
        returncode=1,
    )

    # Invoking the build will raise an error.
    build_command.verify_app_tools(first_app)
    with pytest.raises(BriefcaseCommandError):
        build_command.build_app(first_app)

    # linuxdeploy was invoked
    app_dir = (
        tmp_path / "base_path" / "linux" / "appimage" / "First App" / "First App.AppDir"
    )
    build_command._subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path / "briefcase" / "tools" / "linuxdeploy-wonky.AppImage"
            ),
            "--appdir",
            os.fsdecode(app_dir),
            "--desktop-file",
            os.fsdecode(app_dir / "com.example.first-app.desktop"),
            "--output",
            "appimage",
            "--deploy-deps-only",
            os.fsdecode(app_dir / "usr" / "app" / "support"),
            "--deploy-deps-only",
            os.fsdecode(app_dir / "usr" / "app_packages" / "firstlib"),
            "--deploy-deps-only",
            os.fsdecode(app_dir / "usr" / "app_packages" / "secondlib"),
        ],
        env={
            "PATH": "/usr/local/bin:/usr/bin:/path/to/somewhere",
            "VERSION": "0.0.1",
            "DISABLE_COPYRIGHT_FILES_DEPLOYMENT": "1",
            "APPIMAGE_EXTRACT_AND_RUN": "1",
            "ARCH": "wonky",
        },
        cwd=os.fsdecode(tmp_path / "base_path" / "linux"),
        text=True,
        encoding=mock.ANY,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # chmod isn't invoked if the binary wasn't created.
    assert build_command.tools.os.chmod.call_count == 0


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_build_appimage_in_docker(build_command, first_app, tmp_path, monkeypatch):
    """A Linux app can be packaged as an AppImage in a docker container."""

    # Enable docker, and move to a non-Linux OS.
    build_command.tools.host_os = "TestOS"
    build_command.use_docker = True

    # Provide Docker app context
    build_command.tools[first_app].app_context = DockerAppContext(
        tools=build_command.tools,
        app=first_app,
    )
    build_command.tools[first_app].app_context.prepare(
        image_tag=f"briefcase/com.example.first-app:py3.{sys.version_info.minor}",
        dockerfile_path=tmp_path
        / "base_path"
        / "linux"
        / "appimage"
        / "First App"
        / "Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_platform_path=tmp_path / "base_path" / "linux",
        host_data_path=tmp_path / "briefcase",
        python_version=f"3.{sys.version_info.minor}",
    )

    build_command.build_app(first_app)

    # linuxdeploy was invoked inside Docker
    build_command._subprocess.Popen.assert_called_with(
        [
            "docker",
            "run",
            "--volume",
            f"{build_command.platform_path}:/app:z",
            "--volume",
            f"{build_command.data_path}:/home/brutus/.cache/briefcase:z",
            "--rm",
            "--env",
            "VERSION=0.0.1",
            "--env",
            "DISABLE_COPYRIGHT_FILES_DEPLOYMENT=1",
            "--env",
            "APPIMAGE_EXTRACT_AND_RUN=1",
            "--env",
            "ARCH=wonky",
            f"briefcase/com.example.first-app:py3.{sys.version_info.minor}",
            "/home/brutus/.cache/briefcase/tools/linuxdeploy-wonky.AppImage",
            "--appdir",
            "/app/appimage/First App/First App.AppDir",
            "--desktop-file",
            "/app/appimage/First App/First App.AppDir/com.example.first-app.desktop",
            "--output",
            "appimage",
            "--deploy-deps-only",
            "/app/appimage/First App/First App.AppDir/usr/app/support",
            "--deploy-deps-only",
            "/app/appimage/First App/First App.AppDir/usr/app_packages/firstlib",
            "--deploy-deps-only",
            "/app/appimage/First App/First App.AppDir/usr/app_packages/secondlib",
        ],
        cwd=os.fsdecode(tmp_path / "base_path" / "linux"),
        text=True,
        encoding=mock.ANY,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    # Binary is marked executable
    build_command.tools.os.chmod.assert_called_with(
        tmp_path / "base_path" / "linux" / "First_App-0.0.1-wonky.AppImage", 0o755
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_build_appimage_with_plugins_in_docker(build_command, first_app, tmp_path):
    """A Linux app can be packaged as an AppImage with plugins in a Docker
    container."""
    # Mock the existence of some plugins
    gtk_plugin_path = (
        tmp_path
        / "briefcase"
        / "tools"
        / "linuxdeploy_plugins"
        / "gtk"
        / "linuxdeploy-plugin-gtk.sh"
    )
    gtk_plugin_path.parent.mkdir(parents=True)
    gtk_plugin_path.touch()

    local_file_plugin_path = tmp_path / "local" / "linuxdeploy-plugin-something.sh"
    local_file_plugin_path.parent.mkdir(parents=True)
    local_file_plugin_path.touch()

    # Configure the app to use the plugins
    first_app.linuxdeploy_plugins = [
        "DEPLOY_GTK_VERSION=3 gtk",
        os.fsdecode(local_file_plugin_path),
    ]

    build_command._subprocess.check_output.return_value = "/docker/bin:/docker/sbin"

    # Enable docker, and move to a non-Linux OS.
    build_command.tools.host_os = "TestOS"
    build_command.use_docker = True

    # Provide Docker app context
    build_command.tools[first_app].app_context = DockerAppContext(
        tools=build_command.tools,
        app=first_app,
    )
    build_command.tools[first_app].app_context.prepare(
        image_tag=f"briefcase/com.example.first-app:py3.{sys.version_info.minor}",
        dockerfile_path=tmp_path
        / "base_path"
        / "linux"
        / "appimage"
        / "First App"
        / "Dockerfile",
        app_base_path=tmp_path / "base_path",
        host_platform_path=tmp_path / "base_path" / "linux",
        host_data_path=tmp_path / "briefcase",
        python_version=f"3.{sys.version_info.minor}",
    )

    build_command.build_app(first_app)

    # linuxdeploy was invoked inside Docker
    build_command._subprocess.Popen.assert_called_with(
        [
            "docker",
            "run",
            "--volume",
            f"{build_command.platform_path}:/app:z",
            "--volume",
            f"{build_command.data_path}:/home/brutus/.cache/briefcase:z",
            "--rm",
            "--env",
            "DEPLOY_GTK_VERSION=3",
            "--env",
            (
                "PATH=/home/brutus/.cache/briefcase/tools/linuxdeploy_plugins/gtk"
                ":/app/appimage/First App:/docker/bin:/docker/sbin"
            ),
            "--env",
            "VERSION=0.0.1",
            "--env",
            "DISABLE_COPYRIGHT_FILES_DEPLOYMENT=1",
            "--env",
            "APPIMAGE_EXTRACT_AND_RUN=1",
            "--env",
            "ARCH=wonky",
            f"briefcase/com.example.first-app:py3.{sys.version_info.minor}",
            "/home/brutus/.cache/briefcase/tools/linuxdeploy-wonky.AppImage",
            "--appdir",
            "/app/appimage/First App/First App.AppDir",
            "--desktop-file",
            "/app/appimage/First App/First App.AppDir/com.example.first-app.desktop",
            "--output",
            "appimage",
            "--deploy-deps-only",
            "/app/appimage/First App/First App.AppDir/usr/app/support",
            "--deploy-deps-only",
            "/app/appimage/First App/First App.AppDir/usr/app_packages/firstlib",
            "--deploy-deps-only",
            "/app/appimage/First App/First App.AppDir/usr/app_packages/secondlib",
            "--plugin",
            "gtk",
            "--plugin",
            "something",
        ],
        cwd=os.fsdecode(tmp_path / "base_path" / "linux"),
        text=True,
        encoding=mock.ANY,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    # Local plugin marked executable
    build_command.tools.os.chmod.assert_any_call(
        tmp_path
        / "base_path"
        / "linux"
        / "appimage"
        / "First App"
        / "linuxdeploy-plugin-something.sh",
        0o755,
    )
    # Binary is marked executable
    build_command.tools.os.chmod.assert_called_with(
        tmp_path / "base_path" / "linux" / "First_App-0.0.1-wonky.AppImage", 0o755
    )
