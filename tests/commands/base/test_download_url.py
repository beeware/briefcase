from unittest import mock

import pytest

from briefcase.exceptions import (
    BadNetworkResourceError,
    MissingNetworkResourceError
)


def test_new_download_oneshot(base_command):
    base_command.requests = mock.MagicMock()
    response = mock.MagicMock()
    response.url = 'https://example.com/path/to/something.zip'
    response.status_code = 200
    response.headers.get.return_value = None
    response.content = b'all content'
    base_command.requests.get.return_value = response

    # Download the file
    filename = base_command.download_url(
        url='https://example.com/support?useful=Yes',
        download_path=base_command.base_path / 'downloads',
    )

    # requests.get has been invoked, but content isn't iterated
    base_command.requests.get.assert_called_with(
        'https://example.com/support?useful=Yes',
        stream=True,
    )
    response.headers.get.assert_called_once_with('content-length')
    response.iter_content.assert_not_called()

    # The filename is derived from the URL
    assert filename == base_command.base_path / 'downloads' / 'something.zip'

    # File content is as expected
    with (base_command.base_path / 'downloads' / 'something.zip').open() as f:
        assert f.read() == 'all content'


def test_new_download_chunked(base_command):
    base_command.requests = mock.MagicMock()
    response = mock.MagicMock()
    response.url = 'https://example.com/path/to/something.zip'
    response.status_code = 200
    response.headers.get.return_value = '24'
    response.iter_content.return_value = iter([
        b'chunk-1;',
        b'chunk-2;',
        b'chunk-3;',
    ])
    base_command.requests.get.return_value = response

    # Download the file
    filename = base_command.download_url(
        url='https://example.com/support?useful=Yes',
        download_path=base_command.base_path
    )

    # requests.get has been invoked, and content is chunked.
    base_command.requests.get.assert_called_with(
        'https://example.com/support?useful=Yes',
        stream=True,
    )
    response.headers.get.assert_called_once_with('content-length')
    response.iter_content.assert_called_once_with(chunk_size=1048576)

    # The filename is derived from the URL
    assert filename == base_command.base_path / 'something.zip'

    # The downloaded file exists, and content is as expected
    assert filename.exists()
    with (base_command.base_path / 'something.zip').open() as f:
        assert f.read() == 'chunk-1;chunk-2;chunk-3;'


def test_already_downloaded(base_command):
    # Create an existing file
    existing_file = base_command.base_path / 'something.zip'
    with (existing_file).open('w') as f:
        f.write('existing content')

    base_command.requests = mock.MagicMock()
    response = mock.MagicMock()
    response.url = 'https://example.com/path/to/something.zip'
    response.status_code = 200
    base_command.requests.get.return_value = response

    # Download the file
    filename = base_command.download_url(
        url='https://example.com/support?useful=Yes',
        download_path=base_command.base_path
    )

    # The GET request will have been made
    base_command.requests.get.assert_called_with(
        'https://example.com/support?useful=Yes',
        stream=True,
    )

    # But the request will be abandoned without reading.
    response.headers.get.assert_not_called()

    # but the file existed, so the method returns
    assert filename == existing_file
    assert filename.exists()


def test_missing_resource(base_command):
    base_command.requests = mock.MagicMock()
    response = mock.MagicMock()
    response.status_code = 404

    base_command.requests.get.return_value = response

    # Download the file
    with pytest.raises(MissingNetworkResourceError):
        base_command.download_url(
            url='https://example.com/support?useful=Yes',
            download_path=base_command.base_path
        )

    # requests.get has been invoked, but nothing else.
    base_command.requests.get.assert_called_with(
        'https://example.com/support?useful=Yes',
        stream=True,
    )
    response.headers.get.assert_not_called()

    # The file doesn't exist as a result of the download failure
    assert not (base_command.base_path / 'something.zip').exists()


def test_bad_resource(base_command):
    base_command.requests = mock.MagicMock()
    response = mock.MagicMock()
    response.status_code = 500

    base_command.requests.get.return_value = response

    # Download the file
    with pytest.raises(BadNetworkResourceError):
        base_command.download_url(
            url='https://example.com/support?useful=Yes',
            download_path=base_command.base_path
        )

    # requests.get has been invoked, but nothing else.
    base_command.requests.get.assert_called_with(
        'https://example.com/support?useful=Yes',
        stream=True,
    )
    response.headers.get.assert_not_called()

    # The file doesn't exist as a result of the download failure
    assert not (base_command.base_path / 'something.zip').exists()
