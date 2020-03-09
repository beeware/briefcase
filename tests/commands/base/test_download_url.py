from unittest import mock

import pytest
from urllib3.response import HTTPHeaderDict

from briefcase.exceptions import (
    BadNetworkResourceError,
    MissingNetworkResourceError
)


@pytest.mark.parametrize(
    'url,content_disposition',
    [
        # A `None` value for `content_disposition` means we skip the header.
        # Other values are passed through as HTTP header values.
        ('https://example.com/path/to/something.zip', None),
        # Ensure empty header is ignored.
        ('https://example.com/path/to/something.zip', ''),
        # Paradigmatic case for Content-Disposition: attachment.
        ('https://example.com/path/to/irrelevant.zip',
            'attachment; filename=something.zip'),
        # Ensure extra parameters are ignored.
        ('https://example.com/path/to/irrelevant.zip',
            'attachment; filename=something.zip; ignored=okay'),
        # Ensure garbage headers are ignored.
        ('https://example.com/path/to/something.zip',
            'garbage'),
        # Ensure we respect unusual quoting & case permitted by RFC 6266.
        ('https://example.com/path/to/irrelevant.zip',
            'ATTACHment; filename=    "something.zip"'),
        # Ensure we use filename=, even if filename*= is provided. This makes us a
        # "legacy user agent" in the terms of RFC 6266, for our own simplicity.
        ('https://example.com/path/to/irrelevant.zip',
            'attachment; filename="something.zip"; filename*=utf-8' "''%e2%82%ac%20rates"),
    ]
)
def test_new_download_oneshot(base_command, url, content_disposition):
    base_command.requests = mock.MagicMock()
    response = mock.MagicMock()
    response.url = url
    response.status_code = 200
    response.headers = mock.Mock(wraps=HTTPHeaderDict({
            'content-disposition': content_disposition,
        } if content_disposition is not None else {}))
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
    response.headers.get.assert_called_with('content-length')
    response.iter_content.assert_not_called()

    # The filename is derived from the URL or header
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
    response.headers.get.assert_called_with('content-length')
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
    response.headers.get.return_value = ''
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

    # The request's Content-Disposition header is consumed to
    # examine the filename; the request is abandoned before
    # any other headers are read.
    response.headers.get.assert_called_once_with('Content-Disposition')

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
