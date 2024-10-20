import os
import platform
import shutil
import stat
from collections.abc import Iterable, Iterator
from pathlib import Path
from unittest import mock

import httpx
import pytest

from briefcase.exceptions import (
    BadNetworkResourceError,
    MissingNetworkResourceError,
    NetworkFailure,
)
from briefcase.integrations.base import ToolCache

TEMPORARY_DOWNLOAD_FILE_SUFFIX = ".download"


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.httpx = mock.MagicMock(spec_set=httpx)
    # Restore move so the temporary file can be moved after downloaded
    mock_tools.shutil.move = mock.MagicMock(wraps=shutil.move)
    return mock_tools


class _IteratorByteSteam(httpx.SyncByteStream):
    """Shim that satisfies ``httpx.Response`` ``stream`` parameter type.

    Cannot be replaced by any ``Iterable[bytes]`` because the base class requires
    an explicit finalization method ``close``."""

    def __init__(self, iterable: Iterable[bytes]) -> None:
        self.iterable = iterable

    def __iter__(self) -> Iterator[bytes]:
        return iter(self.iterable)


def _make_httpx_response(
    *,
    url: str,
    status_code: int,
    stream: list[bytes],
    method: str = "GET",
    headers: dict = {},
) -> httpx.Response:
    """Create a real ``httpx.Response`` with key methods wrapped by ``mock.Mock`` for spying.

    Wrapped methods:
        response.read
        response.iter_bytes
        response.headers.get
    """
    response = httpx.Response(
        request=httpx.Request(
            method=method,
            url=httpx.URL(url),
        ),
        status_code=status_code,
        headers=httpx.Headers(headers),
        # Always use ``stream`` rather than content because it's more flexible
        # even if the request is made non-streaming or the response is read with
        # ``response.read()``, httpx will still consume the ``stream`` response
        # content internally. This allows testing both the non-streaming and
        # streaming download paths without needing to complicate the response params
        stream=_IteratorByteSteam(stream),
    )

    response.read = mock.Mock(wraps=response.read)
    response.iter_bytes = mock.Mock(wraps=response.iter_bytes)
    response.headers.get = mock.Mock(wraps=response.headers.get)

    return response


@pytest.fixture
def file_perms() -> int:
    """The expected permissions for the downloaded file.

    Since umask can vary on different systems, it is updated to a known value and reset
    after the test finishes.

    On Windows, the umask seems to always be zero and chmod doesn't really do anything
    anyway.
    """
    if platform.system() == "Windows":
        yield 0o666
    else:
        orig_umask = os.umask(0o077)
        yield 0o600
        os.umask(orig_umask)


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
def test_new_download_oneshot(mock_tools, file_perms, url, content_disposition):
    """If no content-length is provided, ``File`` downloadds the file all at once."""
    response = _make_httpx_response(
        method="GET",
        url=url,
        status_code=200,
        headers=(
            {
                "content-disposition": content_disposition,
            }
            if content_disposition is not None
            else {}
        ),
        stream=[b"all content"],
    )
    mock_tools.httpx.stream.return_value.__enter__.return_value = response

    # Download the file
    filename = mock_tools.file.download(
        url="https://example.com/support?useful=Yes",
        download_path=mock_tools.base_path / "downloads",
    )

    # httpx.stream has been invoked, but content isn't iterated
    mock_tools.httpx.stream.assert_called_with(
        "GET",
        "https://example.com/support?useful=Yes",
        follow_redirects=True,
    )
    response.headers.get.assert_called_with("content-length")
    response.read.assert_called_once()

    # The filename is derived from the URL or header
    assert filename == mock_tools.base_path / "downloads/something.zip"

    # Temporary file was created in download dir and was renamed
    temp_filename = Path(mock_tools.shutil.move.call_args_list[0].args[0])
    assert temp_filename.parent == mock_tools.base_path / "downloads"
    assert temp_filename.name.startswith("something.zip.")
    assert temp_filename.name.endswith(TEMPORARY_DOWNLOAD_FILE_SUFFIX)
    mock_tools.shutil.move.assert_called_with(str(temp_filename), filename)

    # File permissions were set
    mock_tools.os.chmod.assert_called_with(filename, file_perms)
    assert stat.S_IMODE(os.stat(filename).st_mode) == file_perms

    # Attempt to delete Temporary file was made
    mock_tools.os.remove.assert_called_with(str(temp_filename))

    # File content is as expected
    with (mock_tools.base_path / "downloads/something.zip").open(encoding="utf-8") as f:
        assert f.read() == "all content"


def test_new_download_chunked(mock_tools, file_perms):
    """If a content-length is provided, ``File`` streams the response rather than downloading it all at once."""
    response = _make_httpx_response(
        method="GET",
        url="https://example.com/path/to/something.zip",
        status_code=200,
        headers={"content-length": "24"},
        stream=[
            b"chunk-1;",
            b"chunk-2;",
            b"chunk-3;",
        ],
    )
    mock_tools.httpx.stream.return_value.__enter__.return_value = response

    # Download the file
    filename = mock_tools.file.download(
        url="https://example.com/support?useful=Yes",
        download_path=mock_tools.base_path,
    )

    # httpx.stream has been invoked, and content is chunked.
    mock_tools.httpx.stream.assert_called_with(
        "GET",
        "https://example.com/support?useful=Yes",
        follow_redirects=True,
    )
    response.headers.get.assert_called_with("content-length")
    response.iter_bytes.assert_called_once_with(chunk_size=1048576)

    # The filename is derived from the URL
    assert filename == mock_tools.base_path / "something.zip"

    # Temporary file was created in download dir and was renamed
    temp_filename = Path(mock_tools.shutil.move.call_args_list[0].args[0])
    assert temp_filename.parent == mock_tools.base_path
    assert temp_filename.name.startswith("something.zip.")
    assert temp_filename.name.endswith(TEMPORARY_DOWNLOAD_FILE_SUFFIX)
    mock_tools.shutil.move.assert_called_with(str(temp_filename), filename)

    # File permissions were set
    mock_tools.os.chmod.assert_called_with(filename, file_perms)
    assert stat.S_IMODE(os.stat(filename).st_mode) == file_perms

    # Attempt to delete Temporary file was made
    mock_tools.os.remove.assert_called_with(str(temp_filename))

    # The downloaded file exists, and content is as expected
    assert filename.exists()
    with (mock_tools.base_path / "something.zip").open(encoding="utf-8") as f:
        assert f.read() == "chunk-1;chunk-2;chunk-3;"


def test_already_downloaded(mock_tools):
    """If the file already exists on disk, it isn't re-downloaded.

    The request is still made to derive the filename, but the content
    is never streamed."""

    # Create an existing file
    existing_file = mock_tools.base_path / "something.zip"
    with existing_file.open("w", encoding="utf-8") as f:
        f.write("existing content")

    url = "https://example.com/path/to/something.zip"

    response = _make_httpx_response(
        status_code=200,
        url=url,
        # Use content and a content-encoding that would cause a DecodeError
        # if ``File`` tried to read the response content.
        # Because the file already exists, ``File`` shouldn't try to read
        # the response, and the ``DecodingError`` won't occur.
        headers={"content-length": "100", "content-encoding": "gzip"},
        stream=[b"definitely not gzip content"],
    )
    mock_tools.httpx.stream.return_value.__enter__.return_value = response

    # Download the file
    filename = mock_tools.file.download(
        url=url,
        download_path=mock_tools.base_path,
    )

    # The GET request will have been made
    mock_tools.httpx.stream.assert_called_with(
        "GET",
        url,
        follow_redirects=True,
    )

    # The request's Content-Disposition header is consumed to
    # examine the filename; the request is abandoned before
    # any other headers are read.
    response.headers.get.assert_called_once_with("Content-Disposition")

    # but the file existed, so the method returns
    assert filename == existing_file
    assert filename.exists()

    # Temporary file was not created, moved, or deleted
    mock_tools.shutil.move.assert_not_called()
    mock_tools.os.chmod.assert_not_called()
    mock_tools.os.remove.assert_not_called()


def test_missing_resource(mock_tools):
    """MissingNetworkResourceError raises for 404 status code"""
    url = "https://example.com/something.zip?useful=Yes"
    response = _make_httpx_response(
        url=url,
        status_code=404,
        stream=[],
    )

    mock_tools.httpx.stream.return_value.__enter__.return_value = response

    # Download the file
    with pytest.raises(MissingNetworkResourceError):
        mock_tools.file.download(
            url=url,
            download_path=mock_tools.base_path,
        )

    # httpx.stream has been invoked, but nothing else.
    mock_tools.httpx.stream.assert_called_with(
        "GET",
        url,
        follow_redirects=True,
    )
    response.headers.get.assert_not_called()

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()

    # Temporary file was not created, moved, or deleted
    mock_tools.shutil.move.assert_not_called()
    mock_tools.os.chmod.assert_not_called()
    mock_tools.os.remove.assert_not_called()


def test_bad_resource(mock_tools):
    """BadNetworkResourceError raises for non-200 status code"""
    url = "https://example.com/something.zip?useful=Yes"
    response = _make_httpx_response(
        status_code=500,
        url=url,
        stream=[],
    )

    mock_tools.httpx.stream.return_value.__enter__.return_value = response

    # Download the file
    with pytest.raises(BadNetworkResourceError):
        mock_tools.file.download(
            url=url,
            download_path=mock_tools.base_path,
        )

    # httpx.stream has been invoked, but nothing else.
    mock_tools.httpx.stream.assert_called_with(
        "GET",
        url,
        follow_redirects=True,
    )
    response.headers.get.assert_not_called()

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()

    # Temporary file was not created, moved, or deleted
    mock_tools.shutil.move.assert_not_called()
    mock_tools.os.chmod.assert_not_called()
    mock_tools.os.remove.assert_not_called()


def test_iter_bytes_connection_error(mock_tools):
    """NetworkFailure raised if response.iter_bytes() errors
    and cleans up temporary files."""
    url = "https://example.com/something.zip?useful=Yes"
    response = _make_httpx_response(
        status_code=200,
        url=url,
        # Force a real DecodingError by setting the response encoding to
        # gzip with response content that is _not_ gzip
        headers={"content-length": "100", "content-encoding": "gzip"},
        stream=[b"definitely not gzip content"],
    )
    mock_tools.httpx.stream.return_value.__enter__.return_value = response

    # Download the file
    with pytest.raises(NetworkFailure, match="Unable to download something.zip"):
        mock_tools.file.download(
            url="https://example.com/something.zip?useful=Yes",
            download_path=mock_tools.base_path,
        )

    # httpx.stream has been invoked, but nothing else.
    mock_tools.httpx.stream.assert_called_with(
        "GET",
        "https://example.com/something.zip?useful=Yes",
        follow_redirects=True,
    )
    response.headers.get.assert_called_with("content-length")

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()

    # Temporary file was not moved
    mock_tools.shutil.move.assert_not_called()
    mock_tools.os.chmod.assert_not_called()

    # Failure happens during response streaming, so the temporary file is create
    # but then also correctly cleaned up after the failure
    temp_filename = Path(mock_tools.os.remove.call_args_list[0].args[0])
    assert temp_filename.parent == mock_tools.base_path
    assert temp_filename.name.startswith("something.zip.")
    assert temp_filename.name.endswith(TEMPORARY_DOWNLOAD_FILE_SUFFIX)
    mock_tools.os.remove.assert_called_with(str(temp_filename))


def test_connection_error(mock_tools):
    """NetworkFailure raised if the connection fails."""
    # Use ftp scheme to force raising a real ProtocolError without needing to mock
    url = "ftp://example.com/something.zip"

    # Use the real httpx for this test instead of the MagicMock'd one from mock_tools
    # Keep using the fixture though, so that it still gets cleaned up after the test
    mock_tools.httpx = mock.Mock(wraps=httpx)

    # Failure leads to filename never being read, so the error message will use the full URL
    # rather than the filename
    with pytest.raises(NetworkFailure, match=f"Unable to download {url}"):
        mock_tools.file.download(
            url=url,
            download_path=mock_tools.base_path,
        )

    # httpx.stream has been invoked, but nothing else.
    mock_tools.httpx.stream.assert_called_with(
        "GET",
        url,
        follow_redirects=True,
    )

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()

    # Temporary file was never created because the failure happens before a response
    # is every received
    assert not (mock_tools.base_path / "something.zip.download").exists()

    # Temporary file was not created, moved, or deleted
    mock_tools.shutil.move.assert_not_called()
    mock_tools.os.chmod.assert_not_called()
    mock_tools.os.remove.assert_not_called()


def test_redirect_connection_error(mock_tools):
    """NetworkFailure raises if the request leads to too many redirects."""
    mock_tools.httpx.stream.side_effect = [
        httpx.TooManyRedirects("Exceeded max redirects")
    ]

    # Download the file
    with pytest.raises(
        NetworkFailure,
        match=r"Unable to download https\:\/\/example.com\/something\.zip\?useful=Yes",
    ):
        mock_tools.file.download(
            url="https://example.com/something.zip?useful=Yes",
            download_path=mock_tools.base_path,
        )

    # httpx.stream has been invoked, but nothing else.
    mock_tools.httpx.stream.assert_called_with(
        "GET",
        "https://example.com/something.zip?useful=Yes",
        follow_redirects=True,
    )

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()

    # Temporary file was not created, moved, or deleted
    mock_tools.shutil.move.assert_not_called()
    mock_tools.os.chmod.assert_not_called()
    mock_tools.os.remove.assert_not_called()
