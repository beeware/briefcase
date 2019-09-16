from unittest import mock
import zipfile

import pytest
from requests import exceptions as requests_exceptions

from briefcase.commands import CreateCommand
from briefcase.commands.create import InvalidSupportPackage
from briefcase.exceptions import NetworkFailure

from ...utils import SimpleAppConfig


class DummyCreateCommand(CreateCommand):
    def __init__(self, support_file=None):
        super().__init__(platform='tester', output_format='dummy')

        self.support_file = support_file

    @property
    def template_url(self):
        return 'https://github.com/beeware/briefcase-sample-template.git'

    def bundle_path(self, app, base_path):
        raise NotImplementedError()

    def binary_path(self, app, base_path):
        raise NotImplementedError()

    @property
    def support_package_url(self):
        return 'https://example.com/path/to/support.zip'

    def support_path(self, app, base_path):
        return base_path / 'path' / 'to' / 'support'

    def verify_tools(self):
        pass


@pytest.fixture
def myapp():
    return SimpleAppConfig(
        name='myapp',
    )


def test_install_app_support_package(myapp, tmp_path):
    "A support package can be unpacked where it is needed"
    command = DummyCreateCommand()

    # Write a temporary support zip file
    support_file = tmp_path / 'out.zip'
    with zipfile.ZipFile(str(support_file), 'w') as support_zip:
        support_zip.writestr('internal/file.txt', data='hello world')

    # Modify download_url to return the temp zipfile
    command.download_url = mock.MagicMock(return_value=support_file)

    # Install the support package
    command.install_app_support_package(myapp, tmp_path)

    # Confirm that the full path to the support file
    # has been unpacked.
    assert (tmp_path / 'path' / 'to' / 'support' / 'internal' / 'file.txt').exists()


def test_offline_install(myapp, tmp_path):
    "If the computer is offline, an error is raised"
    command = DummyCreateCommand()

    command.download_url = mock.MagicMock(
        side_effect=requests_exceptions.ConnectionError
    )

    # Installing while offline raises an error
    with pytest.raises(NetworkFailure):
        command.install_app_support_package(myapp, tmp_path)


def test_invalid_support_package(myapp, tmp_path):
    "If the support package isn't a valid zipfile, an error si raised"
    command = DummyCreateCommand()

    # Create a support package that isn't a zipfile
    support_file = tmp_path / 'out.zip'
    with open(str(support_file), 'w') as bad_support_zip:
        bad_support_zip.write("This isn't a zip file")

    # Make the download URL return the temp file
    command.download_url = mock.MagicMock(return_value=support_file)

    # Installing the bad support package raises an error
    with pytest.raises(InvalidSupportPackage):
        command.install_app_support_package(myapp, tmp_path)
