import os
import shutil
import sys
from unittest import mock

import httpx
import pytest

from briefcase.exceptions import (
    InvalidStubBinary,
    MissingNetworkResourceError,
    MissingStubBinary,
    NetworkFailure,
)

from ...utils import create_file, create_tgz_file, create_zip_file, mock_zip_download


@pytest.mark.parametrize("console_app", [True, False])
def test_install_stub_binary(
    create_command,
    myapp,
    console_app,
    stub_binary_revision_path_index,
    tmp_path,
):
    """A stub binary can be downloaded and unpacked where it is needed."""
    # Mock the app type
    myapp.console_app = console_app
    stub_name = "Console-Stub" if console_app else "GUI-Stub"

    # Mock download.file to return a stub binary
    create_command.tools.file.download = mock.MagicMock(
        side_effect=mock_zip_download(
            f"{stub_name}-3.X-b37.zip",
            [("Stub.bin", "stub binary")],
        )
    )

    # Wrap shutil so we can confirm that unpack is called
    create_command.tools.shutil = mock.MagicMock(wraps=shutil)

    # Install the stub binary
    create_command.install_stub_binary(myapp)

    # Confirm the right URL was used
    create_command.tools.file.download.assert_called_with(
        download_path=create_command.data_path / "stub",
        url=f"https://briefcase-support.s3.amazonaws.com/python/3.X/Tester/{stub_name}-3.X-b37.zip",
        role="stub binary",
    )

    # Confirm the right file was unpacked
    create_command.tools.shutil.unpack_archive.assert_called_with(
        filename=tmp_path / f"data/stub/{stub_name}-3.X-b37.zip",
        extract_dir=tmp_path / "base_path/build/my-app/tester/dummy",
    )

    # Confirm that the full path to the stub file has been unpacked.
    assert (tmp_path / "base_path/build/my-app/tester/dummy/Stub.bin").exists()


@pytest.mark.parametrize("console_app", [True, False])
def test_install_stub_binary_unpack_failure(
    create_command,
    myapp,
    console_app,
    stub_binary_revision_path_index,
    tmp_path,
):
    """Errors during unpacking the archive raise InvalidStubBinary."""
    # Mock the app type
    myapp.console_app = console_app
    stub_name = "Console-Stub" if console_app else "GUI-Stub"

    # Mock download.file to return a stub binary
    create_command.tools.file.download = mock.MagicMock(
        side_effect=mock_zip_download(
            f"{stub_name}-3.X-b37.zip",
            [("Stub.bin", "stub binary")],
        )
    )

    # Wrap shutil so we can confirm that unpack is called
    create_command.tools.shutil = mock.MagicMock(wraps=shutil)
    create_command.tools.shutil.unpack_archive.side_effect = shutil.ReadError

    # Install the stub binary
    with pytest.raises(InvalidStubBinary, match="Unable to unpack or copy stub binary"):
        create_command.install_stub_binary(myapp)

    # Confirm the right URL was used
    create_command.tools.file.download.assert_called_with(
        download_path=create_command.data_path / "stub",
        url=f"https://briefcase-support.s3.amazonaws.com/python/3.X/Tester/{stub_name}-3.X-b37.zip",
        role="stub binary",
    )

    # Confirm the right file was unpacked
    create_command.tools.shutil.unpack_archive.assert_called_with(
        filename=tmp_path / f"data/stub/{stub_name}-3.X-b37.zip",
        extract_dir=tmp_path / "base_path/build/my-app/tester/dummy",
    )


@pytest.mark.parametrize("console_app", [True, False])
def test_install_pinned_stub_binary(
    create_command,
    myapp,
    console_app,
    stub_binary_revision_path_index,
    tmp_path,
):
    """The stub binary revision can be pinned."""
    # Pin the stub binary revision
    myapp.stub_binary_revision = 42

    # Mock the app type
    myapp.console_app = console_app
    stub_name = "Console-Stub" if console_app else "GUI-Stub"

    # Mock download.file to return a stub binary
    create_command.tools.file.download = mock.MagicMock(
        side_effect=mock_zip_download(
            f"{stub_name}-3.X-b42.zip",
            [("Stub.bin", "stub binary")],
        )
    )

    # Wrap shutil so we can confirm that unpack is called
    create_command.tools.shutil = mock.MagicMock(wraps=shutil)

    # Install the stub binary
    create_command.install_stub_binary(myapp)

    # Confirm the right URL was used
    create_command.tools.file.download.assert_called_with(
        download_path=create_command.data_path / "stub",
        url=f"https://briefcase-support.s3.amazonaws.com/python/3.X/Tester/{stub_name}-3.X-b42.zip",
        role="stub binary",
    )

    # Confirm the right file was unpacked
    create_command.tools.shutil.unpack_archive.assert_called_with(
        filename=tmp_path / f"data/stub/{stub_name}-3.X-b42.zip",
        extract_dir=tmp_path / "base_path/build/my-app/tester/dummy",
    )

    # Confirm that the full path to the stub file has been unpacked.
    assert (tmp_path / "base_path/build/my-app/tester/dummy/Stub.bin").exists()


def test_install_stub_binary_missing(
    create_command,
    myapp,
    stub_binary_revision_path_index,
    tmp_path,
):
    """If the system-nominated stub binary doesn't exist, a specific error is raised."""
    # Modify download.file to raise an exception
    create_command.tools.file.download = mock.MagicMock(
        side_effect=MissingNetworkResourceError(
            "https://briefcase-support.s3.amazonaws.com/python/3.X/Tester/GUI-Stub-3.X-b37.zip"
        )
    )

    # Install the stub binary; this will raise a custom exception
    with pytest.raises(
        MissingStubBinary,
        match=r"Unable to download Tester stub binary for Python 3.X on gothic",
    ):
        create_command.install_stub_binary(myapp)


def test_install_custom_stub_binary_url(
    create_command,
    myapp,
    stub_binary_revision_path_index,
    tmp_path,
):
    """A stub binary can be downloaded and unpacked where it is needed."""
    # Provide an app-specific override of the stub binary as a URL
    myapp.stub_binary = "https://example.com/custom/My-Stub.zip"

    # Mock download.file to return a stub binary
    create_command.tools.file.download = mock.MagicMock(
        side_effect=mock_zip_download(
            "My-Stub.zip",
            [("Stub.bin", "stub binary")],
        )
    )

    # Wrap shutil so we can confirm that unpack is called
    create_command.tools.shutil = mock.MagicMock(wraps=shutil)

    # Install the stub binary
    create_command.install_stub_binary(myapp)

    # Confirm the right URL was used
    create_command.tools.file.download.assert_called_with(
        download_path=create_command.data_path
        / "stub/986428ef9d5a1852fc15d4367f19aa328ad530686056e9d83cdde03407c0bceb",
        url="https://example.com/custom/My-Stub.zip",
        role="stub binary",
    )

    # Confirm the right file was unpacked
    create_command.tools.shutil.unpack_archive.assert_called_with(
        filename=tmp_path
        / "data/stub/986428ef9d5a1852fc15d4367f19aa328ad530686056e9d83cdde03407c0bceb/My-Stub.zip",
        extract_dir=tmp_path / "base_path/build/my-app/tester/dummy",
    )

    # Confirm that the full path to the stub file has been unpacked.
    assert (tmp_path / "base_path/build/my-app/tester/dummy/Stub.bin").exists()


def test_install_custom_stub_binary_file(
    create_command,
    myapp,
    tmp_path,
    stub_binary_revision_path_index,
):
    """A custom stub binary can be specified as a local file."""
    # Provide an app-specific override of the stub binary
    myapp.stub_binary = os.fsdecode(tmp_path / "custom/My-Stub")

    # Write a temporary stub binary
    create_file(tmp_path / "custom/My-Stub", "Custom stub")

    # Modify download.file to return the temp zipfile
    create_command.tools.file.download = mock.MagicMock()

    # Wrap shutil so we can confirm that unpack is called
    create_command.tools.shutil = mock.MagicMock(wraps=shutil)

    # Install the stub binary
    create_command.install_stub_binary(myapp)

    # There should have been no download attempt,
    # as the resource is local.
    create_command.tools.file.download.assert_not_called()

    # The file isn't an archive, so it hasn't been unpacked.
    create_command.tools.shutil.unpack_archive.assert_not_called()

    # Confirm that the full path to the stub file has been unpacked.
    assert (tmp_path / "base_path/build/my-app/tester/dummy/Stub.bin").exists()


def test_install_custom_stub_binary_zip(
    create_command,
    myapp,
    tmp_path,
    stub_binary_revision_path_index,
):
    """A custom stub binary can be specified as a local archive."""
    # Provide an app-specific override of the stub binary
    myapp.stub_binary = os.fsdecode(tmp_path / "custom/stub.zip")

    # Write a temporary stub zip file
    stub_file = create_zip_file(
        tmp_path / "custom/stub.zip",
        [("Stub.bin", "Custom stub")],
    )

    # Modify download.file to return the temp zipfile
    create_command.tools.file.download = mock.MagicMock()

    # Wrap shutil so we can confirm that unpack is called
    create_command.tools.shutil = mock.MagicMock(wraps=shutil)

    # Install the stub binary
    create_command.install_stub_binary(myapp)

    # There should have been no download attempt,
    # as the resource is local.
    create_command.tools.file.download.assert_not_called()

    # Confirm the right file was unpacked
    create_command.tools.shutil.unpack_archive.assert_called_with(
        filename=stub_file,
        extract_dir=tmp_path / "base_path/build/my-app/tester/dummy",
    )

    # Confirm that the full path to the stub file has been unpacked.
    assert (tmp_path / "base_path/build/my-app/tester/dummy/Stub.bin").exists()


@pytest.mark.parametrize("stub_filename", ("stub.tar", "stub.tar.gz"))
def test_install_custom_stub_binary_tar(
    create_command,
    myapp,
    stub_filename,
    tmp_path,
    stub_binary_revision_path_index,
):
    """A custom stub binary can be specified as a local archive."""
    # Provide an app-specific override of the stub binary
    myapp.stub_binary = os.fsdecode(tmp_path / f"custom/{stub_filename}")

    # Write a temporary stub zip file
    stub_file = create_tgz_file(
        tmp_path / f"custom/{stub_filename}",
        [("Stub.bin", "Custom stub")],
    )

    # Modify download.file to return the temp zipfile
    create_command.tools.file.download = mock.MagicMock()

    # Wrap shutil so we can confirm that unpack is called
    create_command.tools.shutil = mock.MagicMock(wraps=shutil)

    # Install the stub binary
    create_command.install_stub_binary(myapp)

    # There should have been no download attempt,
    # as the resource is local.
    create_command.tools.file.download.assert_not_called()

    # Confirm the right file was unpacked
    create_command.tools.shutil.unpack_archive.assert_called_with(
        filename=stub_file,
        extract_dir=tmp_path / "base_path/build/my-app/tester/dummy",
        **({"filter": "data"} if sys.version_info >= (3, 12) else {}),
    )

    # Confirm that the full path to the stub file has been unpacked.
    assert (tmp_path / "base_path/build/my-app/tester/dummy/Stub.bin").exists()


def test_install_custom_stub_binary_with_revision(
    create_command,
    myapp,
    tmp_path,
    stub_binary_revision_path_index,
    capsys,
):
    """If a custom stub binary file also specifies a revision, the revision is ignored
    with a warning."""
    # Provide an app-specific override of the stub binary, *and* the revision
    myapp.stub_binary = os.fsdecode(tmp_path / "custom/stub.zip")
    myapp.stub_binary_revision = "42"

    # Write a temporary stub zip file
    stub_file = create_zip_file(
        tmp_path / "custom/stub.zip",
        [("Stub.bin", "Custom stub")],
    )

    # Modify download.file to return the temp zipfile
    create_command.tools.file.download = mock.MagicMock()

    # Wrap shutil so we can confirm that unpack is called
    create_command.tools.shutil = mock.MagicMock(wraps=shutil)

    # Install the stub binary
    create_command.install_stub_binary(myapp)

    # There should have been no download attempt,
    # as the resource is local.
    create_command.tools.file.download.assert_not_called()

    # Confirm the right file was unpacked
    create_command.tools.shutil.unpack_archive.assert_called_with(
        filename=stub_file,
        extract_dir=tmp_path / "base_path/build/my-app/tester/dummy",
    )

    # Confirm that the full path to the stub file has been unpacked.
    assert (tmp_path / "base_path/build/my-app/tester/dummy/Stub.bin").exists()

    # A warning about the stub revision was generated.
    assert "stub binary revision will be ignored." in capsys.readouterr().out


def test_install_custom_stub_binary_with_invalid_url(
    create_command,
    myapp,
    stub_binary_revision_path_index,
):
    """Invalid URL for a custom stub binary raises MissingNetworkResourceError."""

    # Provide a custom stub binary URL
    url = "https://example.com/custom/stub.zip"
    myapp.stub_binary = url

    # Modify download.file to raise an exception
    create_command.tools.file.download = mock.MagicMock(
        side_effect=MissingNetworkResourceError(url)
    )

    # The bad URL should raise a MissingNetworkResourceError
    with pytest.raises(MissingNetworkResourceError):
        create_command.install_stub_binary(myapp)

    # However, there will have been a download attempt
    create_command.tools.file.download.assert_called_with(
        download_path=(
            create_command.data_path
            / "stub"
            / "8d0f202db2a2c66b1568ead0ca63f66957bd2be7a12145f5b9fa2197a5e049f7"
        ),
        url=url,
        role="stub binary",
    )


def test_offline_install(
    create_command,
    myapp,
    stub_binary_revision_path_index,
):
    """If the computer is offline, an error is raised."""
    stream_mock = create_command.tools.httpx.stream = mock.MagicMock()
    stream_mock.return_value.__enter__.side_effect = httpx.TransportError(
        "Unstable connection"
    )

    # Installing while offline raises an error
    with pytest.raises(NetworkFailure):
        create_command.install_stub_binary(myapp)


def test_install_custom_stub_binary_with_invalid_filepath(
    create_command,
    myapp,
    stub_binary_revision_path_index,
    tmp_path,
):
    """Invalid file path for custom stub library raises InvalidStubBinary."""
    # Provide an app-specific override of the stub binary
    myapp.stub_binary = os.fsdecode(tmp_path / "custom/My-Stub")

    # Modify download.file to return the temp zipfile
    create_command.tools.file.download = mock.MagicMock()

    # Mock shutil so we can confirm that unpack isn't called,
    # but we still want the side effect of calling
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.shutil.copyfile.side_effect = shutil.copyfile

    # Fail to install the stub binary
    with pytest.raises(InvalidStubBinary, match="Unable to unpack or copy stub binary"):
        create_command.install_stub_binary(myapp)

    # There should have been no download attempt,
    # as the resource is local.
    create_command.tools.file.download.assert_not_called()

    # The file isn't an archive, so it hasn't been unpacked.
    create_command.tools.shutil.unpack_archive.assert_not_called()
