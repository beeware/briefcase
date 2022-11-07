import os
import platform
import shutil
import stat
from pathlib import Path
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

TEMPORARY_DOWNLOAD_FILE_SUFFIX = ".download"


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.requests = mock.MagicMock(spec_set=requests)
    # Restore move so the temporary file can be moved after downloaded
    mock_tools.shutil.move = mock.MagicMock(wraps=shutil.move)
    return mock_tools


@pytest.fixture
def file_perms() -> int:
    """The expected permissions for the downloaded file.

    Since umask can vary on different systems, it is updated to a known
    value and reset after the test finishes.

    On Windows, the umask seems to always be zero and chmod doesn't really
    do anything anyway.
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
    with (mock_tools.base_path / "downloads" / "something.zip").open() as f:
        assert f.read() == "all content"


def test_new_download_chunked(mock_tools, file_perms):
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

    # Temporary file was not created, moved, or deleted
    mock_tools.shutil.move.assert_not_called()
    mock_tools.os.chmod.assert_not_called()
    mock_tools.os.remove.assert_not_called()


def test_missing_resource(mock_tools):
    response = mock.MagicMock()
    response.status_code = 404

    mock_tools.requests.get.return_value = response

    # Download the file
    with pytest.raises(MissingNetworkResourceError):
        mock_tools.download.file(
            url="https://example.com/something.zip?useful=Yes",
            download_path=mock_tools.base_path,
        )

    # requests.get has been invoked, but nothing else.
    mock_tools.requests.get.assert_called_with(
        "https://example.com/something.zip?useful=Yes",
        stream=True,
    )
    response.headers.get.assert_not_called()

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()

    # Temporary file was not created, moved, or deleted
    mock_tools.shutil.move.assert_not_called()
    mock_tools.os.chmod.assert_not_called()
    mock_tools.os.remove.assert_not_called()


def test_bad_resource(mock_tools):
    response = mock.MagicMock()
    response.status_code = 500

    mock_tools.requests.get.return_value = response

    # Download the file
    with pytest.raises(BadNetworkResourceError):
        mock_tools.download.file(
            url="https://example.com/something.zip?useful=Yes",
            download_path=mock_tools.base_path,
        )

    # requests.get has been invoked, but nothing else.
    mock_tools.requests.get.assert_called_with(
        "https://example.com/something.zip?useful=Yes",
        stream=True,
    )
    response.headers.get.assert_not_called()

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()

    # Temporary file was not created, moved, or deleted
    mock_tools.shutil.move.assert_not_called()
    mock_tools.os.chmod.assert_not_called()
    mock_tools.os.remove.assert_not_called()


def test_get_connection_error(mock_tools):
    """NetworkFailure raises if requests.get() errors."""
    mock_tools.requests.get.side_effect = requests.exceptions.ConnectionError

    # Download the file
    with pytest.raises(
        NetworkFailure,
        match=r"Unable to download https\:\/\/example.com\/something\.zip\?useful=Yes",
    ):
        mock_tools.download.file(
            url="https://example.com/something.zip?useful=Yes",
            download_path=mock_tools.base_path,
        )

    # requests.get has been invoked, but nothing else.
    mock_tools.requests.get.assert_called_with(
        "https://example.com/something.zip?useful=Yes",
        stream=True,
    )

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()

    # Temporary file was not created, moved, or deleted
    mock_tools.shutil.move.assert_not_called()
    mock_tools.os.chmod.assert_not_called()
    mock_tools.os.remove.assert_not_called()


def test_iter_content_connection_error(mock_tools):
    """NetworkFailure raised if response.iter_content() errors."""
    response = mock.MagicMock(spec=requests.Response)
    response.url = "https://example.com/something.zip?useful=Yes"
    response.headers = mock.Mock(wraps=HTTPHeaderDict({"content-length": "100"}))
    response.status_code = 200
    response.iter_content.side_effect = requests.exceptions.ConnectionError
    mock_tools.requests.get.return_value = response

    # Download the file
    with pytest.raises(NetworkFailure, match="Unable to download something.zip"):
        mock_tools.download.file(
            url="https://example.com/something.zip?useful=Yes",
            download_path=mock_tools.base_path,
        )

    # requests.get has been invoked, but nothing else.
    mock_tools.requests.get.assert_called_with(
        "https://example.com/something.zip?useful=Yes",
        stream=True,
    )
    response.headers.get.assert_called_with("content-length")

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()

    # Temporary file was not moved
    mock_tools.shutil.move.assert_not_called()
    mock_tools.os.chmod.assert_not_called()

    # Temporary file was created and named appropriately and then deleted
    temp_filename = Path(mock_tools.os.remove.call_args_list[0].args[0])
    assert temp_filename.parent == mock_tools.base_path
    assert temp_filename.name.startswith("something.zip.")
    assert temp_filename.name.endswith(TEMPORARY_DOWNLOAD_FILE_SUFFIX)
    mock_tools.os.remove.assert_called_with(str(temp_filename))


def test_content_connection_error(mock_tools):
    """NetworkFailure raised if response.content errors."""
    response = mock.MagicMock(spec=requests.Response)
    response.url = "https://example.com/something.zip?useful=Yes"
    response.headers = mock.Mock(wraps=HTTPHeaderDict())
    response.status_code = 200
    type(response).content = mock.PropertyMock(
        side_effect=requests.exceptions.ConnectionError
    )
    mock_tools.requests.get.return_value = response

    # Download the file
    with pytest.raises(NetworkFailure, match="Unable to download something.zip"):
        mock_tools.download.file(
            url="https://example.com/something.zip?useful=Yes",
            download_path=mock_tools.base_path,
        )

    # requests.get has been invoked, but nothing else.
    mock_tools.requests.get.assert_called_with(
        "https://example.com/something.zip?useful=Yes",
        stream=True,
    )
    response.headers.get.assert_called_with("content-length")

    # The file doesn't exist as a result of the download failure
    assert not (mock_tools.base_path / "something.zip").exists()

    # Temporary file was not moved but it was deleted
    mock_tools.shutil.move.assert_not_called()
    mock_tools.os.chmod.assert_not_called()

    # Temporary file was created and named appropriately and then deleted
    temp_filename = Path(mock_tools.os.remove.call_args_list[0].args[0])
    assert temp_filename.parent == mock_tools.base_path
    assert temp_filename.name.startswith("something.zip.")
    assert temp_filename.name.endswith(TEMPORARY_DOWNLOAD_FILE_SUFFIX)
    mock_tools.os.remove.assert_called_with(str(temp_filename))
