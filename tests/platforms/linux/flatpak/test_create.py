import platform
import shutil
import sys
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.platforms.linux.flatpak import LinuxFlatpakCreateCommand


@pytest.mark.parametrize(
    "sys_version_info, platform_version, url",
    [
        (
            (3, 10, 5, "final", 0),
            "3.10.5",
            "https://www.python.org/ftp/python/3.10.5/Python-3.10.5.tgz",
        ),
        (
            (3, 11, 0, "beta", 1),
            "3.11.0b1",
            "https://www.python.org/ftp/python/3.11.0/Python-3.11.0b1.tgz",
        ),
    ],
)
def test_support_package_url(tmp_path, sys_version_info, platform_version, url):
    """The support package URL is customized."""
    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    # Mock the responses from system version APIs
    command.tools.sys = mock.MagicMock(spec_set=sys)
    command.tools.sys.version_info = sys_version_info

    command.tools.platform = mock.MagicMock(spec_set=platform)
    command.tools.platform.python_version.return_value = platform_version

    assert command.support_package_url(52) == url


def test_output_format_template_context(first_app_config, tmp_path):
    """The template context is provided flatpak details."""
    first_app_config.flatpak_runtime = "org.beeware.Platform"
    first_app_config.flatpak_runtime_version = "37.42"
    first_app_config.flatpak_sdk = "org.beeware.SDK"

    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    assert command.output_format_template_context(first_app_config) == {
        "flatpak_runtime": "org.beeware.Platform",
        "flatpak_runtime_version": "37.42",
        "flatpak_sdk": "org.beeware.SDK",
    }


def test_install_support_package(first_app_config, tmp_path):
    """Support files are copied into place, rather than being unpacked."""
    command = LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.shutil = mock.MagicMock(spec_set=shutil)
    command.tools.download.file = mock.MagicMock(
        return_value=tmp_path / "support" / "Python-3.X.Y.tgz"
    )

    command.install_app_support_package(first_app_config)

    # The support file was copied into place
    command.tools.shutil.copy.assert_called_once_with(
        tmp_path / "support" / "Python-3.X.Y.tgz",
        tmp_path / "base_path" / "linux" / "flatpak" / "First App" / "Python-3.X.Y.tgz",
    )
