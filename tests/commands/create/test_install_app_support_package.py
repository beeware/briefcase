from pathlib import Path
from unittest import mock
import zipfile

import pytest
from requests import exceptions as requests_exceptions

from briefcase.commands.create import InvalidSupportPackage
from briefcase.exceptions import NetworkFailure


def test_install_app_support_package(create_command, myapp, tmp_path, support_path):
    "A support package can be unpacked where it is needed"
    # Hardcode the support package URL for test purposes
    create_command._support_package_url = 'https://example.com/path/to/support.zip'

    # Write a temporary support zip file
    support_file = tmp_path / 'out.zip'
    with zipfile.ZipFile(str(support_file), 'w') as support_zip:
        support_zip.writestr('internal/file.txt', data='hello world')

    # Modify download_url to return the temp zipfile
    create_command.download_url = mock.MagicMock(return_value=support_file)

    # Install the support package
    create_command.install_app_support_package(myapp, tmp_path)

    # Confirm the right URL was used
    create_command.download_url.assert_called_with(
        download_path=Path.home() / '.briefcase' / 'support',
        url='https://example.com/path/to/support.zip',
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / 'internal' / 'file.txt').exists()


def test_install_custom_app_support_package(create_command, myapp, tmp_path, support_path):
    "A custom support package can be specified"
    # Hardcode the support package URL for test purposes
    create_command._support_package_url = 'https://example.com/path/to/support.zip'

    # Provide an app-specific override of the package URL
    myapp.support_package_url = 'https://example.com/custom/support.zip'

    # Write a temporary support zip file
    support_file = tmp_path / 'out.zip'
    with zipfile.ZipFile(str(support_file), 'w') as support_zip:
        support_zip.writestr('internal/file.txt', data='hello world')

    # Modify download_url to return the temp zipfile
    create_command.download_url = mock.MagicMock(return_value=support_file)

    # Install the support package
    create_command.install_app_support_package(myapp, tmp_path)

    # Confirm the right URL was used
    create_command.download_url.assert_called_with(
        download_path=Path.home() / '.briefcase' / 'support',
        url='https://example.com/custom/support.zip',
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / 'internal' / 'file.txt').exists()


def test_offline_install(create_command, myapp, tmp_path, support_path):
    "If the computer is offline, an error is raised"
    # Hardcode the support package URL for test purposes
    create_command._support_package_url = 'https://example.com/path/to/support.zip'

    create_command.download_url = mock.MagicMock(
        side_effect=requests_exceptions.ConnectionError
    )

    # Installing while offline raises an error
    with pytest.raises(NetworkFailure):
        create_command.install_app_support_package(myapp, tmp_path)


def test_invalid_support_package(create_command, myapp, tmp_path, support_path):
    "If the support package isn't a valid zipfile, an error is raised"
    # Hardcode the support package URL for test purposes
    create_command._support_package_url = 'https://example.com/path/to/support.zip'

    # Create a support package that isn't a zipfile
    support_file = tmp_path / 'out.zip'
    with open(str(support_file), 'w') as bad_support_zip:
        bad_support_zip.write("This isn't a zip file")

    # Make the download URL return the temp file
    create_command.download_url = mock.MagicMock(return_value=support_file)

    # Installing the bad support package raises an error
    with pytest.raises(InvalidSupportPackage):
        create_command.install_app_support_package(myapp, tmp_path)
