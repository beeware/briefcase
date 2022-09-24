from unittest import mock

import pytest
import requests
import requests.exceptions
from urllib3._collections import HTTPHeaderDict

from briefcase.exceptions import (
    BadNetworkResourceError,
    MissingNetworkResourceError,
    NetworkFailure,
)
from briefcase.integrations.base import ToolCache


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.requests = mock.MagicMock(spec_set=requests)
    return mock_tools


@pytest.mark.parametrize(
    "url,content_disposition",
    [
        # A `None` value for `content_disposition` means we skip the header.
        # Other values are passed through as HTTP header values.
        ("https://example.com/path/to/something.zip", None),
        # Ensure empty header is ignored.
        ("https://example.com/path/to/something.zip", ""),
        # Paradigmatic case for Content-Disposition: attachment.
        (
            "https://example.com/path/to/irrelevant.zip",
            "attachment; filename=something.zip",
        ),
        # Ensure extra parameters are ignored.
        (
            "https://example.com/path/to/irrelevant.zip",
            "attachment; filename=something.zip; ignored=okay",
        ),
        # Ensure garbage headers are ignored.
        ("https://example.com/path/to/something.zip", "garbage"),
        # Ensure we respect unusual quoting & case permitted by RFC 6266.
        (
            "https://example.com/path/to/irrelevant.zip",
            'ATTACHment; filename=    "something.zip"',
        ),
        # Ensure we use filename=, even if filename*= is provided. This makes us a
        # "legacy user agent" in the terms of RFC 6266, for our own simplicity.
        (
            "https://example.com/path/to/irrelevant.zip",
            'attachment; filename="something.zip"; filename*=utf-8'
            "''%e2%82%ac%20rates",
        ),
    ],
)
def test_new_download_oneshot(mock_tools, url, content_disposition):
    response = mock.MagicMock(spec=requests.Response)
    response.url = url
    response.status_code = 200
    response.headers = mock.Mock(
        wraps=HTTPHeaderDict(
            {
                "content-disposition": content_disposition,
            }
            if content_disposition is not None
            else {}
        )
    )
    response.content = b"all content"
    mock_tools.requests.get.return_value = response

    # Download the file
    filename = mock_tools.download.file(
        url="https://example.com/support?useful=Yes",
        download_path=mock_tools.base_path / "downloads",
    )

    # requests.get has been invoked, but content isn't iterated
    mock_tools.requests.get.assert_called_with(
        "https://example.com/support?useful=Yes",
        stream=True,
    )
    response.headers.get.assert_called_with("content-length")
    response.iter_content.assert_not_called()

    # The filename is derived from the URL or header
    assert filename == mock_tools.base_path / "downloads" / "something.zip"

    # File content is as expected
    with (mock_tools.base_path / "downloads" / "something.zip").open() as f:
        assert f.read() == "all content"


def test_new_download_chunked(mock_tools):
    response = mock.MagicMock()
    response.url = "https://example.com/path/to/something.zip"
    response.status_code = 200
    response.headers.get.return_value = "24"
    response.iter_content.return_value = iter(
        [
            b"chunk-1;",
            b"chunk-2;",
            b"chunk-3;",
        ]
    )
    mock_tools.requests.get.return_value = response

    # Download the file
    filename = mock_tools.download.file(
        url="https://example.com/support?useful=Yes",
        download_path=mock_tools.base_path,
    )

    # requests.get has been invoked, and content is chunked.
    mock_tools.requests.get.assert_called_with(
        "https://example.com/support?useful=Yes",
        stream=True,
    )
    response.headers.get.assert_called_with("content-length")
    response.iter_content.assert_called_once_with(chunk_size=1048576)

    # The filename is derived from the URL
    assert filename == mock_tools.base_path / "something.zip"

    # The downloaded file exists, and content is as expected
    assert filename.exists()
    with (mock_tools.base_path / "something.zip").open() as f:
        assert f.read() == "chunk-1;chunk-2;chunk-3;"


def test_already_downloaded(mock_tools):
    # Create an existing file
    existing_file = mock_tools.base_path / "something.zip"
    with existing_file.open("w") as f:
        f.write("existing content")

    response = mock.MagicMock()
    response.headers.get.return_value = ""
    response.url = "https://example.com/path/to/something.zip"
    response.status_code = 200
    mock_tools.requests.get.return_value = response

    # Download the file
    filename = mock_tools.download.file(
        url="https://example.com/support?useful=Yes",
        download_path=mock_tools.base_path,
    )

    # The GET request will have been made
    mock_tools.requests.get.assert_called_with(
        "https://example.com/support?useful=Yes",
        stream=True,
    )

    # The request's Content-Disposition header is consumed to
    # examine the filename; the request is abandoned before
    # any other headers are read.
    response.headers.get.assert_called_once_with("Content-Disposition")

    # but the file existed, so the method returns
    assert filename == existing_file
    assert filename.exists()


def test_missing_resource(mock_tools):
    response = mock.MagicMock()
    response.status_code = 404

    mock_tools.requests.get.return_value = response

    # Download the file
    with pytest.raises(MissingNetworkResourceError):
        mock_tools.download.file(
            url="https://example.com/support?useful=Yes",
            download_path=mock_tools.base_path,
        )

    # requests.get has been invoked, but nothing else.
    mock_tools.requests.get.assert_called_with(
        "https://example.com/support?useful=Yes",
        stream=True,
    )
    response.headers.get.assert_not_called()

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()


def test_bad_resource(mock_tools):
    response = mock.MagicMock()
    response.status_code = 500

    mock_tools.requests.get.return_value = response

    # Download the file
    with pytest.raises(BadNetworkResourceError):
        mock_tools.download.file(
            url="https://example.com/support?useful=Yes",
            download_path=mock_tools.base_path,
        )

    # requests.get has been invoked, but nothing else.
    mock_tools.requests.get.assert_called_with(
        "https://example.com/support?useful=Yes",
        stream=True,
    )
    response.headers.get.assert_not_called()

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()


def test_get_connection_error(mock_tools):
    """NetworkFailure raises if requests.get() errors."""
    mock_tools.requests.get.side_effect = requests.exceptions.ConnectionError

    # Download the file
    with pytest.raises(
        NetworkFailure,
        match=r"Unable to download https\:\/\/example.com\/support\?useful=Yes",
    ):
        mock_tools.download.file(
            url="https://example.com/support?useful=Yes",
            download_path=mock_tools.base_path,
        )

    # requests.get has been invoked, but nothing else.
    mock_tools.requests.get.assert_called_with(
        "https://example.com/support?useful=Yes",
        stream=True,
    )

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()


def test_iter_content_connection_error(mock_tools):
    """NetworkFailure raised if response.iter_content() errors."""
    response = mock.MagicMock(spec=requests.Response)
    response.url = "https://example.com/support?useful=Yes"
    response.headers = mock.Mock(wraps=HTTPHeaderDict({"content-length": "100"}))
    response.status_code = 200
    response.iter_content.side_effect = requests.exceptions.ConnectionError
    mock_tools.requests.get.return_value = response

    # Download the file
    with pytest.raises(NetworkFailure, match="Unable to download support"):
        mock_tools.download.file(
            url="https://example.com/support?useful=Yes",
            download_path=mock_tools.base_path,
        )

    # requests.get has been invoked, but nothing else.
    mock_tools.requests.get.assert_called_with(
        "https://example.com/support?useful=Yes",
        stream=True,
    )
    response.headers.get.assert_called_with("content-length")

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()


def test_content_connection_error(mock_tools):
    """NetworkFailure raised if response.content errors."""

    response = mock.MagicMock(spec=requests.Response)
    response.url = "https://example.com/support?useful=Yes"
    response.headers = mock.Mock(wraps=HTTPHeaderDict())
    response.status_code = 200
    type(response).content = mock.PropertyMock(
        side_effect=requests.exceptions.ConnectionError
    )
    mock_tools.requests.get.return_value = response

    # Download the file
    with pytest.raises(NetworkFailure, match="Unable to download support"):
        mock_tools.download.file(
            url="https://example.com/support?useful=Yes",
            download_path=mock_tools.base_path,
        )

    # requests.get has been invoked, but nothing else.
    mock_tools.requests.get.assert_called_with(
        "https://example.com/support?useful=Yes",
        stream=True,
    )
    response.headers.get.assert_called_with("content-length")

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()
