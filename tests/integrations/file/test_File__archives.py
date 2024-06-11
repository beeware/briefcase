import shutil
import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="module")
def custom_packing_format():
    shutil.register_unpack_format(
        "custom_packing",
        [".archive", ".archive.ext"],
        lambda x, y: True,
    )
    yield
    shutil.unregister_unpack_format("custom_packing")


@pytest.mark.parametrize(
    "filename, outcome",
    [
        ("filename.tar", True),
        ("filename.zip", True),
        ("filename.archive", True),
        ("filename.part.archive", True),
        ("filename.archive.ext", True),
        ("filename.part.archive.ext", True),
        ("filename.part.archive.ext", True),
        ("filename", False),
        ("filename.doc", False),
        ("filename.archive.doc", False),
        ("filename.archive.ext.doc", False),
    ],
)
@pytest.mark.usefixtures("custom_packing_format")
def test_is_archive(mock_tools, filename, outcome, monkeypatch):
    """Archive filenames are properly detected."""
    assert mock_tools.file.is_archive(filename) is outcome


def test_unpack_archive(mock_tools):
    """Archive unpacking is deferred correctly for an arbitrary archive."""
    mock_tools.shutil = MagicMock(spec=shutil)

    mock_tools.file.unpack_archive(
        "test_archive",
        extract_dir="destination",
    )

    mock_tools.shutil.unpack_archive.assert_called_once_with(
        filename="test_archive",
        extract_dir="destination",
        **({"filter": "data"} if sys.version_info >= (3, 12) else {}),
    )


def test_unpack_archive_kwargs(mock_tools):
    """Archive unpacking is deferred correctly with kwargs."""
    mock_tools.shutil = MagicMock(spec=shutil)

    mock_tools.file.unpack_archive(
        "test_archive",
        extract_dir="destination",
        extra_arg="arg this",
    )

    mock_tools.shutil.unpack_archive.assert_called_once_with(
        filename="test_archive",
        extract_dir="destination",
        **(
            {"filter": "data", "extra_arg": "arg this"}
            if sys.version_info >= (3, 12)
            else {"extra_arg": "arg this"}
        ),
    )


def test_unpack_archive_override_filter(mock_tools):
    """Archive unpacking is deferred correctly while overriding `filter`."""
    mock_tools.shutil = MagicMock(spec=shutil)

    mock_tools.file.unpack_archive(
        "test_archive",
        extract_dir="destination",
        filter="onlycatpics",
        extra_arg="arg this",
    )

    mock_tools.shutil.unpack_archive.assert_called_once_with(
        filename="test_archive",
        extract_dir="destination",
        filter="onlycatpics",
        extra_arg="arg this",
    )


def test_unpack_zip_archive(mock_tools):
    """Archive unpacking is deferred correctly for ZIP archives."""
    mock_tools.shutil = MagicMock(spec=shutil)

    mock_tools.file.unpack_archive(
        "test_archive.zip",
        extract_dir="destination",
    )

    mock_tools.shutil.unpack_archive.assert_called_once_with(
        filename="test_archive.zip",
        extract_dir="destination",
    )


def test_unpack_zip_archive_kwargs(mock_tools):
    """Archive unpacking is deferred correctly for ZIP archives with kwargs."""
    mock_tools.shutil = MagicMock(spec=shutil)

    mock_tools.file.unpack_archive(
        "test_archive.zip",
        extract_dir="destination",
        extra_arg="arg this",
    )

    mock_tools.shutil.unpack_archive.assert_called_once_with(
        filename="test_archive.zip",
        extract_dir="destination",
        extra_arg="arg this",
    )
