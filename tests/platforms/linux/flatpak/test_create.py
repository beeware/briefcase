from unittest import mock

import pytest

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
    command = LinuxFlatpakCreateCommand(base_path=tmp_path)

    # Mock the responses from system version APIs
    command.sys = mock.MagicMock()
    command.sys.version_info = sys_version_info

    command.stdlib_platform = mock.MagicMock()
    command.stdlib_platform.python_version.return_value = platform_version

    assert command.support_package_url == url


def test_output_format_template_context(first_app_config, tmp_path):
    """The template context is provided flatpak details."""
    first_app_config.flatpak_runtime = "org.beeware.Platform"
    first_app_config.flatpak_runtime_version = "37.42"
    first_app_config.flatpak_sdk = "org.beeware.SDK"

    command = LinuxFlatpakCreateCommand(base_path=tmp_path)

    assert command.output_format_template_context(first_app_config) == {
        "flatpak_runtime": "org.beeware.Platform",
        "flatpak_runtime_version": "37.42",
        "flatpak_sdk": "org.beeware.SDK",
    }


def test__unpack_support_package(first_app_config, tmp_path):
    """Support files are copied into place, rather than being unpacked."""
    command = LinuxFlatpakCreateCommand(base_path=tmp_path)
    command.shutil = mock.MagicMock()

    command._unpack_support_package(
        first_app_config,
        tmp_path / "support" / "Python-3.X.Y.tgz",
    )

    # The support file was copied into place
    command.shutil.copy.assert_called_once_with(
        tmp_path / "support" / "Python-3.X.Y.tgz",
        tmp_path / "linux" / "flatpak" / "First App" / "Python-3.X.Y.tgz",
    )


def test_install_app_dependencies(first_app_config, tmp_path):
    """Installing app dependencies creates a requirements file."""
    # Set up some app dependencies.
    first_app_config.requires = [
        "toga-gtk>=0.3.0.dev35",
        "pillow",
        "../../path/to/code",
        "git+https://github.com/beeware/gbulb.git",
    ]

    command = LinuxFlatpakCreateCommand(base_path=tmp_path)

    # Create the bundle path
    command.bundle_path(first_app_config).mkdir(parents=True)

    # Install dependencies into the bundle
    command.install_app_dependencies(first_app_config)

    # A requirements file has been created with the expected content
    requirements_txt = tmp_path / "linux" / "flatpak" / "First App" / "requirements.txt"
    assert requirements_txt.exists()
    with requirements_txt.open() as f:
        assert f.read() == (
            "toga-gtk>=0.3.0.dev35\n"
            "pillow\n"
            "../../path/to/code\n"
            "git+https://github.com/beeware/gbulb.git\n"
        )


def test_no_install_app_dependencies(first_app_config, tmp_path):
    """If an app has no dependencies, a requirements file is still written."""
    command = LinuxFlatpakCreateCommand(base_path=tmp_path)

    # Create the bundle path
    command.bundle_path(first_app_config).mkdir(parents=True)

    # Install dependencies into the bundle
    command.install_app_dependencies(first_app_config)

    # An empty requirements file has been created
    requirements_txt = tmp_path / "linux" / "flatpak" / "First App" / "requirements.txt"
    assert requirements_txt.exists()
    with requirements_txt.open() as f:
        assert f.read() == ""
