from unittest import mock

import pytest

from briefcase.commands.base import BaseCommand
from briefcase.exceptions import (
    BadNetworkResourceError,
    MissingNetworkResourceError
)


class DummyCommand(BaseCommand):
    """
    A dummy command to test the BaseCommand interface.
    """
    def __init__(self):
        super().__init__(platform='tester', output_format='dummy')

    def bundle_path(self, app, base_path):
        raise NotImplementedError()

    def binary_path(self, app, base_path):
        raise NotImplementedError()


def test_new_download_oneshot(tmp_path):
    command = DummyCommand()

    command.requests = mock.MagicMock()
    response = mock.MagicMock()
    response.status_code = 200

    response.headers.get.return_value = None
    response.content = b'all content'

    command.requests.get.return_value = response

    # Download the file
    filename = command.download_url(
        url='https://example.com/path/to/something.zip',
        download_path=tmp_path / 'downloads',
    )

    # requests.get has been invoked, but content isn't iterated
    command.requests.get.assert_called_with(
        'https://example.com/path/to/something.zip',
        stream=True,
    )
    response.headers.get.assert_called_once_with('content-length')
    response.iter_content.assert_not_called()

    # The filename is derived from the URL
    assert filename == tmp_path / 'downloads' / 'something.zip'

    # File content is as expected
    with open(tmp_path / 'downloads' / 'something.zip') as f:
        assert f.read() == 'all content'


def test_new_download_chunked(tmp_path):
    command = DummyCommand()

    command.requests = mock.MagicMock()
    response = mock.MagicMock()
    response.status_code = 200

    command.requests.get.return_value = response

    response.headers.get.return_value = '24'
    response.iter_content.return_value = iter([
        b'chunk-1;',
        b'chunk-2;',
        b'chunk-3;',
    ])

    # Download the file
    filename = command.download_url(
        url='https://example.com/path/to/something.zip',
        download_path=tmp_path
    )

    # requests.get has been invoked, and content is chunked.
    command.requests.get.assert_called_with(
        'https://example.com/path/to/something.zip',
        stream=True,
    )
    response.headers.get.assert_called_once_with('content-length')
    response.iter_content.assert_called_once_with(chunk_size=1048576)

    # The filename is derived from the URL
    assert filename == tmp_path / 'something.zip'

    # The downloaded file exists, and content is as expected
    assert filename.exists()
    with open(tmp_path / 'something.zip') as f:
        assert f.read() == 'chunk-1;chunk-2;chunk-3;'


def test_already_downloaded(tmp_path):
    # Create an existing file
    existing_file = tmp_path / 'something.zip'
    with open(existing_file, 'w') as f:
        f.write('existing content')

    command = DummyCommand()
    command.requests = mock.MagicMock()

    # Download the file
    filename = command.download_url(
        url='https://example.com/path/to/something.zip',
        download_path=tmp_path
    )

    # Nothing was downloaded
    command.requests.get.assert_not_called()

    # but the file existed, so the method returns
    assert filename == existing_file
    assert filename.exists()


def test_missing_resource(tmp_path):
    command = DummyCommand()

    command.requests = mock.MagicMock()
    response = mock.MagicMock()
    response.status_code = 404

    command.requests.get.return_value = response

    # Download the file
    with pytest.raises(MissingNetworkResourceError):
        command.download_url(
            url='https://example.com/path/to/something.zip',
            download_path=tmp_path
        )

    # requests.get has been invoked, but nothing else.
    command.requests.get.assert_called_with(
        'https://example.com/path/to/something.zip',
        stream=True,
    )
    response.headers.get.assert_not_called()

    # The file doesn't exist as a result of the download failure
    assert not (tmp_path / 'something.zip').exists()


def test_bad_resource(tmp_path):
    command = DummyCommand()

    command.requests = mock.MagicMock()
    response = mock.MagicMock()
    response.status_code = 500

    command.requests.get.return_value = response

    # Download the file
    with pytest.raises(BadNetworkResourceError):
        command.download_url(
            url='https://example.com/path/to/something.zip',
            download_path=tmp_path
        )

    # requests.get has been invoked, but nothing else.
    command.requests.get.assert_called_with(
        'https://example.com/path/to/something.zip',
        stream=True,
    )
    response.headers.get.assert_not_called()

    # The file doesn't exist as a result of the download failure
    assert not (tmp_path / 'something.zip').exists()
