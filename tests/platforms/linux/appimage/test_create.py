import sys
from unittest.mock import MagicMock

import pytest

from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand


def test_support_package_url(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)

    # Set some properties of the host system for test purposes.
    command.host_arch = 'wonky'
    command.platform = 'tester'

    assert command.support_package_url_query == [
        ('platform', 'tester'),
        ('version', '3.{minor}'.format(minor=sys.version_info.minor)),
        ('arch', 'wonky'),
    ]


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows paths aren't converted in Docker context"
)
def test_install_app_dependencies(first_app_config, tmp_path):
    "If Docker is in use, a docker context is used to invoke pip"
    first_app_config.requires = ['foo==1.2.3', 'bar>=4.5']

    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.use_docker = True
    command.subprocess = MagicMock()
    docker = MagicMock()
    command.Docker = MagicMock()
    command.Docker.return_value = docker

    command._path_index = {
        first_app_config: {
            'app_packages_path': 'path/to/app_packages'
        }
    }

    command.install_app_dependencies(first_app_config)

    # A docker context was created
    command.Docker.assert_called_with(command, first_app_config)

    # The docker container was prepared
    docker.prepare.assert_called_with()

    # pip was invoked inside docker.
    docker.run.assert_called_with(
        [
            sys.executable, '-m', 'pip',
            'install', '--upgrade', '--no-user',
            '--target={tmp_path}/linux/appimage/First App/path/to/app_packages'.format(
                tmp_path=tmp_path
            ),
            'foo==1.2.3',
            'bar>=4.5',
        ],
        check=True
    )


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows paths aren't converted in Docker context"
)
def test_install_app_dependencies_no_docker(first_app_config, tmp_path):
    "If docker is *not* in use, calls are made on raw subprocess"
    first_app_config.requires = ['foo==1.2.3', 'bar>=4.5']

    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    command.use_docker = False
    command.subprocess = MagicMock()
    docker = MagicMock()
    command.Docker = MagicMock()
    command.Docker.return_value = docker

    command._path_index = {
        first_app_config: {
            'app_packages_path': 'path/to/app_packages'
        }
    }

    command.install_app_dependencies(first_app_config)

    # A docker context was not created, nor was it prepared
    assert command.Docker.call_count == 0
    assert docker.prepare.call_count == 0

    # The no-op prepare call was made.
    command.subprocess.prepare.assert_called_with()

    # pip was invoked natively
    command.subprocess.run.assert_called_with(
        [
            sys.executable, '-m', 'pip',
            'install', '--upgrade', '--no-user',
            '--target={tmp_path}/linux/appimage/First App/path/to/app_packages'.format(
                tmp_path=tmp_path
            ),
            'foo==1.2.3',
            'bar>=4.5',
        ],
        check=True
    )
