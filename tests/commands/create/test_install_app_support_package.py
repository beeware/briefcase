import zipfile
from unittest import mock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.commands.create import InvalidSupportPackage
from briefcase.exceptions import NetworkFailure


def test_install_app_support_package(create_command, myapp, tmp_path, support_path):
    "A support package can be downloaded and unpacked where it is needed"
    # Write a temporary support zip file
    support_file = tmp_path / 'out.zip'
    with zipfile.ZipFile(str(support_file), 'w') as support_zip:
        support_zip.writestr('internal/file.txt', data='hello world')

    # Modify download_url to return the temp zipfile
    create_command.download_url = mock.MagicMock(return_value=support_file)

    # Install the support package
    create_command.install_app_support_package(myapp)

    # Confirm the right URL was used
    create_command.download_url.assert_called_with(
        download_path=create_command.dot_briefcase_path / 'support',
        url='https://briefcase-support.org/python?platform=tester&version=3.X',
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / 'internal' / 'file.txt').exists()


def test_install_pinned_app_support_package(create_command, myapp, tmp_path, support_path):
    "A pinned support package can be downloaded and unpacked where it is needed"
    # Pin the support revision
    myapp.support_revision = '42'

    # Write a temporary support zip file
    support_file = tmp_path / 'out.zip'
    with zipfile.ZipFile(str(support_file), 'w') as support_zip:
        support_zip.writestr('internal/file.txt', data='hello world')

    # Modify download_url to return the temp zipfile
    create_command.download_url = mock.MagicMock(return_value=support_file)

    # Install the support package
    create_command.install_app_support_package(myapp)

    # Confirm the right URL was used
    create_command.download_url.assert_called_with(
        download_path=create_command.dot_briefcase_path / 'support',
        url='https://briefcase-support.org/python?platform=tester&version=3.X&revision=42',
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / 'internal' / 'file.txt').exists()


def test_install_custom_app_support_package_file(create_command, myapp, tmp_path, support_path):
    "A custom support package can be specified as a local file"
    # Provide an app-specific override of the package URL
    myapp.support_package = str(tmp_path / 'custom' / 'support.zip')

    # Write a temporary support zip file
    support_file = tmp_path / 'custom' / 'support.zip'
    support_file.parent.mkdir(parents=True)
    with zipfile.ZipFile(str(support_file), 'w') as support_zip:
        support_zip.writestr('internal/file.txt', data='hello world')

    # Modify download_url to return the temp zipfile
    create_command.download_url = mock.MagicMock()

    # Install the support package
    create_command.install_app_support_package(myapp)

    # There should have been no download attempt,
    # as the resource is local.
    create_command.download_url.assert_not_called()

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / 'internal' / 'file.txt').exists()


def test_install_custom_app_support_package_url(create_command, myapp, tmp_path, support_path):
    "A custom support package can be specified as URL"
    # Provide an app-specific override of the package URL
    myapp.support_package = 'https://example.com/custom/support.zip'

    # Write a temporary support zip file
    support_file = tmp_path / 'out.zip'
    with zipfile.ZipFile(str(support_file), 'w') as support_zip:
        support_zip.writestr('internal/file.txt', data='hello world')

    # Modify download_url to return the temp zipfile
    create_command.download_url = mock.MagicMock(return_value=support_file)

    # Install the support package
    create_command.install_app_support_package(myapp)

    # Confirm the right URL was used
    create_command.download_url.assert_called_with(
        download_path=create_command.dot_briefcase_path / 'support',
        url='https://example.com/custom/support.zip',
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / 'internal' / 'file.txt').exists()


def test_install_pinned_custom_app_support_package_url(create_command, myapp, tmp_path, support_path):
    "A custom support package can be specified as URL, and pinned to a revision"
    # Pin the support revision
    myapp.support_revision = '42'

    # Provide an app-specific override of the package URL
    myapp.support_package = 'https://example.com/custom/support.zip'

    # Write a temporary support zip file
    support_file = tmp_path / 'out.zip'
    with zipfile.ZipFile(str(support_file), 'w') as support_zip:
        support_zip.writestr('internal/file.txt', data='hello world')

    # Modify download_url to return the temp zipfile
    create_command.download_url = mock.MagicMock(return_value=support_file)

    # Install the support package
    create_command.install_app_support_package(myapp)

    # Confirm the right URL was used
    create_command.download_url.assert_called_with(
        download_path=create_command.dot_briefcase_path / 'support',
        url='https://example.com/custom/support.zip?revision=42',
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / 'internal' / 'file.txt').exists()


def test_install_pinned_custom_app_support_package_url_with_args(create_command, myapp, tmp_path, support_path):
    "A custom support package can be specified as URL with args, and pinned to a revision"
    # Pin the support revision
    myapp.support_revision = '42'

    # Provide an app-specific override of the package URL
    myapp.support_package = 'https://example.com/custom/support.zip?cool=Yes'

    # Write a temporary support zip file
    support_file = tmp_path / 'out.zip'
    with zipfile.ZipFile(str(support_file), 'w') as support_zip:
        support_zip.writestr('internal/file.txt', data='hello world')

    # Modify download_url to return the temp zipfile
    create_command.download_url = mock.MagicMock(return_value=support_file)

    # Install the support package
    create_command.install_app_support_package(myapp)

    # Confirm the right URL was used
    create_command.download_url.assert_called_with(
        download_path=create_command.dot_briefcase_path / 'support',
        url='https://example.com/custom/support.zip?cool=Yes&revision=42',
    )

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (support_path / 'internal' / 'file.txt').exists()


def test_offline_install(create_command, myapp, support_path):
    "If the computer is offline, an error is raised"
    create_command.download_url = mock.MagicMock(
        side_effect=requests_exceptions.ConnectionError
    )

    # Installing while offline raises an error
    with pytest.raises(NetworkFailure):
        create_command.install_app_support_package(myapp)


def test_invalid_support_package(create_command, myapp, tmp_path, support_path):
    "If the support package isn't a valid zipfile, an error is raised"
    # Create a support package that isn't a zipfile
    support_file = tmp_path / 'out.zip'
    with open(str(support_file), 'w') as bad_support_zip:
        bad_support_zip.write("This isn't a zip file")

    # Make the download URL return the temp file
    create_command.download_url = mock.MagicMock(return_value=support_file)

    # Installing the bad support package raises an error
    with pytest.raises(InvalidSupportPackage):
        create_command.install_app_support_package(myapp)


def test_missing_support_package(create_command, myapp, tmp_path, support_path):
    "If the path provided for the support package is bad, an error is raised"
    # Set a custom support package that doesn't exist
    myapp.support_package = '/path/does/not/exist.zip'

    # Installing the bad support package raises an error
    with pytest.raises(InvalidSupportPackage):
        create_command.install_app_support_package(myapp)
