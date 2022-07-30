import os
import shutil
from unittest import mock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.commands.create import InvalidSupportPackage, MissingSupportPackage
from briefcase.exceptions import MissingNetworkResourceError, NetworkFailure

from ...utils import create_zip_file, mock_file_download, mock_zip_download


def test_install_app_support_package(
    create_command,
    myapp,
    tmp_path,
    support_path,
    app_requirements_path_index,
):
    """A support package can be downloaded and unpacked where it is needed."""

    # Mock download_url to return a support package
    create_command.download_url = mock.MagicMock(
        side_effect=mock_zip_download(
            "Python-3.X-OS-support.zip",
            [("internal/file.txt", "hello world")],
        )
    )

    # Mock shutil so we can confirm that unpack is called,
    # but we still want the side effect of calling it
    create_command.shutil = mock.MagicMock()
    create_command.shutil.unpack_archive.side_effect = shutil.unpack_archive

    # Install the support package
    create_command.install_app_support_package(myapp)

    # Confirm the right URL was used
    create_command.download_url.assert_called_with(
        download_path=create_command.data_path / "support",
        url="https://briefcase-support.org/python?platform=tester&version=3.X&arch=gothic",
    )

    # Confirm the right file was unpacked
    create_command.shutil.unpack_archive.assert_called_with(
        tmp_path / "data" / "support" / "Python-3.X-OS-support.zip",
        extract_dir=support_path,
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / "internal" / "file.txt").exists()


def test_install_pinned_app_support_package(
    create_command,
    myapp,
    tmp_path,
    support_path,
    app_requirements_path_index,
):
    """A pinned support package can be downloaded and unpacked where it is
    needed."""
    # Pin the support revision
    myapp.support_revision = "42"

    # Mock download_url to return a support package
    create_command.download_url = mock.MagicMock(
        side_effect=mock_zip_download(
            "Python-3.X-OS-support.zip",
            [("internal/file.txt", "hello world")],
        )
    )

    # Mock shutil so we can confirm that unpack is called,
    # but we still want the side effect of calling it
    create_command.shutil = mock.MagicMock()
    create_command.shutil.unpack_archive.side_effect = shutil.unpack_archive

    # Install the support package
    create_command.install_app_support_package(myapp)

    # Confirm the right URL was used
    create_command.download_url.assert_called_with(
        download_path=create_command.data_path / "support",
        url="https://briefcase-support.org/python?platform=tester&version=3.X&arch=gothic&revision=42",
    )

    # Confirm the right file was unpacked
    create_command.shutil.unpack_archive.assert_called_with(
        tmp_path / "data" / "support" / "Python-3.X-OS-support.zip",
        extract_dir=support_path,
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / "internal" / "file.txt").exists()


def test_install_custom_app_support_package_file(
    create_command,
    myapp,
    tmp_path,
    support_path,
    app_requirements_path_index,
):
    """A custom support package can be specified as a local file."""
    # Provide an app-specific override of the package URL
    myapp.support_package = os.fsdecode(tmp_path / "custom" / "support.zip")

    # Write a temporary support zip file
    support_file = create_zip_file(
        tmp_path / "custom" / "support.zip",
        [("internal/file.txt", "hello world")],
    )

    # Modify download_url to return the temp zipfile
    create_command.download_url = mock.MagicMock()

    # Mock shutil so we can confirm that unpack is called,
    # but we still want the side effect of calling it
    create_command.shutil = mock.MagicMock()
    create_command.shutil.unpack_archive.side_effect = shutil.unpack_archive

    # Install the support package
    create_command.install_app_support_package(myapp)

    # There should have been no download attempt,
    # as the resource is local.
    create_command.download_url.assert_not_called()

    # Confirm the right file was unpacked
    create_command.shutil.unpack_archive.assert_called_with(
        support_file,
        extract_dir=support_path,
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / "internal" / "file.txt").exists()


def test_support_package_url_with_invalid_custom_support_packge_url(
    create_command,
    myapp,
    app_requirements_path_index,
):
    """Invalid URL for a custom support package raises
    MissingNetworkResourceError."""

    # Provide an custom support URL
    url = "https://example.com/custom/support.zip"
    myapp.support_package = url

    # Modify download_url to raise an exception
    create_command.download_url = mock.MagicMock(
        side_effect=MissingNetworkResourceError(url)
    )

    # The bad URL should raise a MissingNetworkResourceError
    with pytest.raises(MissingNetworkResourceError):
        create_command.install_app_support_package(myapp)

    # However, there will have been a download attempt
    create_command.download_url.assert_called_with(
        download_path=(
            create_command.data_path
            / "support"
            / "55441abbffa311f65622df45a943afc347a21ab40e8dcec79472c92ef467db24"
        ),
        url=url,
    )


def test_support_package_url_with_unsupported_platform(
    create_command,
    myapp,
    app_requirements_path_index,
):
    """An unsupported platform raises MissingSupportPackage."""
    # Set the host architecture to something unsupported
    create_command.host_arch = "unknown"

    # Modify download_url to raise an exception due to missing support package
    create_command.download_url = mock.MagicMock(
        side_effect=MissingNetworkResourceError(
            "https://briefcase-support.org/python?platform=tester&version=3.X&arch=unknown"
        )
    )

    # The unknown platform should cause a missing support package error
    with pytest.raises(MissingSupportPackage):
        create_command.install_app_support_package(myapp)

    # However, there will have been a download attempt
    create_command.download_url.assert_called_with(
        download_path=create_command.data_path / "support",
        url="https://briefcase-support.org/python?platform=tester&version=3.X&arch=unknown",
    )


def test_install_custom_app_support_package_url(
    create_command,
    myapp,
    tmp_path,
    support_path,
    app_requirements_path_index,
):
    """A custom support package can be specified as URL."""
    # Provide an app-specific override of the package URL
    myapp.support_package = "https://example.com/custom/custom-support.zip"

    # Mock download_url to return a support package
    create_command.download_url = mock.MagicMock(
        side_effect=mock_zip_download(
            "custom-support.zip",
            [("internal/file.txt", "hello world")],
        )
    )

    # Mock shutil so we can confirm that unpack is called,
    # but we still want the side effect of calling it
    create_command.shutil = mock.MagicMock()
    create_command.shutil.unpack_archive.side_effect = shutil.unpack_archive

    # Install the support package
    create_command.install_app_support_package(myapp)

    # Confirm the right URL and download path was used
    create_command.download_url.assert_called_with(
        download_path=(
            create_command.data_path
            / "support"
            / "1d3ac0e09eb22abc63c4e7b699b6ab5d58e277015eeae61070e3f9f11512e6b3"
        ),
        url="https://example.com/custom/custom-support.zip",
    )

    # Confirm the right file was unpacked into the hashed location
    create_command.shutil.unpack_archive.assert_called_with(
        tmp_path
        / "data"
        / "support"
        / "1d3ac0e09eb22abc63c4e7b699b6ab5d58e277015eeae61070e3f9f11512e6b3"
        / "custom-support.zip",
        extract_dir=support_path,
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / "internal" / "file.txt").exists()


def test_install_pinned_custom_app_support_package_url(
    create_command,
    myapp,
    tmp_path,
    support_path,
    app_requirements_path_index,
):
    """A custom support package can be specified as URL, and pinned to a
    revision."""
    # Pin the support revision
    myapp.support_revision = "42"

    # Provide an app-specific override of the package URL
    myapp.support_package = "https://example.com/custom/custom-support.zip"

    # Mock download_url to return a support package
    create_command.download_url = mock.MagicMock(
        side_effect=mock_zip_download(
            "custom-support.zip",
            [("internal/file.txt", "hello world")],
        )
    )

    # Mock shutil so we can confirm that unpack is called,
    # but we still want the side effect of calling it
    create_command.shutil = mock.MagicMock()
    create_command.shutil.unpack_archive.side_effect = shutil.unpack_archive

    # Install the support package
    create_command.install_app_support_package(myapp)

    # Confirm the right URL and download path was used
    create_command.download_url.assert_called_with(
        download_path=(
            create_command.data_path
            / "support"
            / "6390bc0eb3eca03218604f6072094d44f44d82eacefc21975cc5b9b7b1720a0d"
        ),
        url="https://example.com/custom/custom-support.zip?revision=42",
    )

    # Confirm the right file was unpacked
    create_command.shutil.unpack_archive.assert_called_with(
        tmp_path
        / "data"
        / "support"
        / "6390bc0eb3eca03218604f6072094d44f44d82eacefc21975cc5b9b7b1720a0d"
        / "custom-support.zip",
        extract_dir=support_path,
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / "internal" / "file.txt").exists()


def test_install_pinned_custom_app_support_package_url_with_args(
    create_command,
    myapp,
    tmp_path,
    support_path,
    app_requirements_path_index,
):
    """A custom support package can be specified as URL with args, and pinned
    to a revision."""
    # Pin the support revision
    myapp.support_revision = "42"

    # Provide an app-specific override of the package URL
    myapp.support_package = "https://example.com/custom/custom-support.zip?cool=Yes"

    # Mock download_url to return a support package
    create_command.download_url = mock.MagicMock(
        side_effect=mock_zip_download(
            "custom-support.zip",
            [("internal/file.txt", "hello world")],
        )
    )
    # Mock shutil so we can confirm that unpack is called,
    # but we still want the side effect of calling it
    create_command.shutil = mock.MagicMock()
    create_command.shutil.unpack_archive.side_effect = shutil.unpack_archive

    # Install the support package
    create_command.install_app_support_package(myapp)

    # Confirm the right URL was used
    create_command.download_url.assert_called_with(
        download_path=create_command.data_path
        / "support"
        / "1a7054ce49ce29aeec90591be2d69cd655bd5414f4a9017425026760a375847b",
        url="https://example.com/custom/custom-support.zip?cool=Yes&revision=42",
    )

    # Confirm the right file was unpacked
    create_command.shutil.unpack_archive.assert_called_with(
        tmp_path
        / "data"
        / "support"
        / "1a7054ce49ce29aeec90591be2d69cd655bd5414f4a9017425026760a375847b"
        / "custom-support.zip",
        extract_dir=support_path,
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / "internal" / "file.txt").exists()


def test_offline_install(
    create_command,
    myapp,
    support_path,
    app_requirements_path_index,
):
    """If the computer is offline, an error is raised."""
    create_command.download_url = mock.MagicMock(
        side_effect=requests_exceptions.ConnectionError
    )

    # Installing while offline raises an error
    with pytest.raises(NetworkFailure):
        create_command.install_app_support_package(myapp)


def test_invalid_support_package(
    create_command,
    myapp,
    tmp_path,
    support_path,
    app_requirements_path_index,
):
    """If the support package isn't a valid zipfile, an error is raised."""
    # Mock download_url to return a non-zip file
    create_command.download_url = mock.MagicMock(
        side_effect=mock_file_download(
            "not-a.zip",
            "This isn't a zip file",
        )
    )

    # Installing the bad support package raises an error
    with pytest.raises(InvalidSupportPackage):
        create_command.install_app_support_package(myapp)


def test_missing_support_package(
    create_command,
    myapp,
    tmp_path,
    support_path,
    app_requirements_path_index,
):
    """If the path provided for the support package is bad, an error is
    raised."""
    # Set a custom support package that doesn't exist
    myapp.support_package = "/path/does/not/exist.zip"

    # Installing the bad support package raises an error
    with pytest.raises(InvalidSupportPackage):
        create_command.install_app_support_package(myapp)


def test_no_support_path(create_command, myapp, no_support_path_index):
    """If support_path is not listed in briefcase.toml, a support package will
    not be downloaded."""
    create_command.download_url = mock.MagicMock()
    create_command.install_app_support_package(myapp)
    create_command.download_url.assert_not_called()
