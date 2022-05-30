import os
import subprocess
import sys
from unittest.mock import MagicMock

import pytest
from requests import exceptions as requests_exceptions

from briefcase.exceptions import BriefcaseCommandError, NetworkFailure
from briefcase.integrations.android_sdk import AndroidSDK
from tests.utils import FsPathMock


@pytest.fixture
def mock_sdk(tmp_path):
    command = MagicMock()
    command.home_path = tmp_path

    # For default test purposes, assume we're on macOS x86_64
    command.host_os = "Darwin"
    command.host_arch = "x86_64"

    sdk = AndroidSDK(command, jdk=MagicMock(), root_path=tmp_path)

    # Mock some existing emulators
    sdk.emulators = MagicMock(
        return_value=[
            "runningEmulator",
            "idleEmulator",
        ]
    )

    return sdk


@pytest.mark.parametrize(
    "host_os, host_arch, emulator_abi",
    [
        ("Darwin", "x86_64", "x86_64"),
        ("Darwin", "arm64", "arm64-v8a"),
        ("Windows", "x86_64", "x86_64"),
        ("Linux", "x86_64", "x86_64"),
    ],
)
def test_create_emulator(mock_sdk, tmp_path, host_os, host_arch, emulator_abi):
    """A new emulator can be created."""
    # This test validates everything going well on first run.
    # This means the skin will be downloaded and unpacked.

    # Mock the hardware and operating system to specific values
    mock_sdk.command.host_os = host_os
    mock_sdk.command.host_arch = host_arch

    # Mock the user providing several invalid names before getting it right.
    mock_sdk.command.input.side_effect = [
        "runningEmulator",
        "invalid name",
        "annoying!",
        "new-emulator",
    ]

    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    if sys.version_info < (3, 8):
        skin_tgz_path = FsPathMock("/path/to/skin.tgz")
    else:
        skin_tgz_path = MagicMock()
        skin_tgz_path.__fspath__.return_value = "/path/to/skin.tgz"
    mock_sdk.command.download_url.return_value = skin_tgz_path

    # Mock the initial output of an AVD config file.
    avd_config_path = tmp_path / ".android" / "avd" / "new-emulator.avd" / "config.ini"
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w") as f:
        f.write("hw.device.name=pixel\n")

    # Create the emulator
    avd = mock_sdk.create_emulator()

    # The expected device AVD was created.
    assert avd == "new-emulator"

    # avdmanager was invoked
    mock_sdk.command.subprocess.check_output.assert_called_once_with(
        [
            os.fsdecode(mock_sdk.avdmanager_path),
            "--verbose",
            "create",
            "avd",
            "--name",
            "new-emulator",
            "--abi",
            emulator_abi,
            "--package",
            f"system-images;android-31;default;{emulator_abi}",
            "--device",
            "pixel",
        ],
        env=mock_sdk.env,
        stderr=subprocess.STDOUT,
    )

    # Skin was downloaded
    mock_sdk.command.download_url.assert_called_once_with(
        url="https://android.googlesource.com/platform/tools/adt/idea/"
        "+archive/refs/heads/mirror-goog-studio-master-dev/"
        "artwork/resources/device-art-resources/pixel_3a.tar.gz",
        download_path=mock_sdk.root_path,
    )

    # Skin is unpacked.
    mock_sdk.command.shutil.unpack_archive.assert_called_once_with(
        skin_tgz_path, extract_dir=mock_sdk.root_path / "skins" / "pixel_3a"
    )

    # Original file was deleted.
    skin_tgz_path.unlink.assert_called_once_with()

    # Emulator configuration file has been appended.
    with avd_config_path.open() as f:
        config = f.read().split("\n")
    assert "hw.keyboard=yes" in config
    assert "skin.name=pixel_3a" in config


def test_create_preexisting_skins(mock_sdk, tmp_path):
    """Test that if skins already exist, they're not re-downloaded."""
    # This test validates that if skins are already cached,
    # they're not re-downloaded

    # Mock the hardware and operating system
    mock_sdk.command.host_os = "Darwin"
    mock_sdk.command.host_arch = "x86_64"

    # Mock the user getting a valid name first time
    mock_sdk.command.input.return_value = "new-emulator"

    # Mock a pre-existing skin folder
    (mock_sdk.root_path / "skins" / "pixel_3a").mkdir(parents=True)

    # Mock the initial output of an AVD config file.
    avd_config_path = tmp_path / ".android" / "avd" / "new-emulator.avd" / "config.ini"
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w") as f:
        f.write("hw.device.name=pixel\n")

    # Create the emulator
    avd = mock_sdk.create_emulator()

    # The expected device AVD was created.
    assert avd == "new-emulator"

    # avdmanager was invoked
    mock_sdk.command.subprocess.check_output.assert_called_once_with(
        [
            os.fsdecode(mock_sdk.avdmanager_path),
            "--verbose",
            "create",
            "avd",
            "--name",
            "new-emulator",
            "--abi",
            "x86_64",
            "--package",
            "system-images;android-31;default;x86_64",
            "--device",
            "pixel",
        ],
        env=mock_sdk.env,
        stderr=subprocess.STDOUT,
    )

    # Skin was not re-downloaded
    assert mock_sdk.command.download_url.call_count == 0

    # Emulator configuration file has been appended.
    with avd_config_path.open() as f:
        config = f.read().split("\n")
    assert "hw.keyboard=yes" in config
    assert "skin.name=pixel_3a" in config


def test_create_failure(mock_sdk):
    """If avdmanager fails, an error is raised."""
    # Mock the user getting a valid name first time
    mock_sdk.command.input.return_value = "new-emulator"

    # Mock an avdmanager failure.
    mock_sdk.command.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(returncode=1, cmd="avdmanager")
    )

    # Create the emulator
    with pytest.raises(BriefcaseCommandError):
        mock_sdk.create_emulator()

    # but avdmanager was invoked
    mock_sdk.command.subprocess.check_output.assert_called_once_with(
        [
            os.fsdecode(mock_sdk.avdmanager_path),
            "--verbose",
            "create",
            "avd",
            "--name",
            "new-emulator",
            "--abi",
            "x86_64",
            "--package",
            "system-images;android-31;default;x86_64",
            "--device",
            "pixel",
        ],
        env=mock_sdk.env,
        stderr=subprocess.STDOUT,
    )


def test_download_failure(mock_sdk, tmp_path):
    """If the skin download fails, an error is raised."""
    # Mock a valid user response.
    mock_sdk.command.input.return_value = "new-emulator"

    # Mock a failure downloading the skin
    mock_sdk.command.download_url.side_effect = requests_exceptions.ConnectionError

    # Create the emulator
    with pytest.raises(NetworkFailure):
        mock_sdk.create_emulator()

    # avdmanager was invoked
    mock_sdk.command.subprocess.check_output.assert_called_once_with(
        [
            os.fsdecode(mock_sdk.avdmanager_path),
            "--verbose",
            "create",
            "avd",
            "--name",
            "new-emulator",
            "--abi",
            "x86_64",
            "--package",
            "system-images;android-31;default;x86_64",
            "--device",
            "pixel",
        ],
        env=mock_sdk.env,
        stderr=subprocess.STDOUT,
    )

    # An attempt was made to download the skin
    mock_sdk.command.download_url.assert_called_once_with(
        url="https://android.googlesource.com/platform/tools/adt/idea/"
        "+archive/refs/heads/mirror-goog-studio-master-dev/"
        "artwork/resources/device-art-resources/pixel_3a.tar.gz",
        download_path=mock_sdk.root_path,
    )

    # Skin wasn't downloaded, so it wasn't unpacked
    assert mock_sdk.command.shutil.unpack_archive.call_count == 0


def test_unpack_failure(mock_sdk, tmp_path):
    """If the download is corrupted and unpacking fails, an error is raised."""
    # Mock a valid user response.
    mock_sdk.command.input.return_value = "new-emulator"

    # Mock the result of the download of a skin
    # Consider to remove if block when we drop py3.7 support, only keep statements from else.
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    if sys.version_info < (3, 8):
        skin_tgz_path = FsPathMock("/path/to/skin.tgz")
    else:
        skin_tgz_path = MagicMock()
        skin_tgz_path.__fspath__.return_value = "/path/to/skin.tgz"
    mock_sdk.command.download_url.return_value = skin_tgz_path

    # Mock a failure unpacking the skin
    mock_sdk.command.shutil.unpack_archive.side_effect = EOFError

    # Create the emulator
    with pytest.raises(BriefcaseCommandError):
        mock_sdk.create_emulator()

    # avdmanager was invoked
    mock_sdk.command.subprocess.check_output.assert_called_once_with(
        [
            os.fsdecode(mock_sdk.avdmanager_path),
            "--verbose",
            "create",
            "avd",
            "--name",
            "new-emulator",
            "--abi",
            "x86_64",
            "--package",
            "system-images;android-31;default;x86_64",
            "--device",
            "pixel",
        ],
        env=mock_sdk.env,
        stderr=subprocess.STDOUT,
    )

    # Skin was downloaded
    mock_sdk.command.download_url.assert_called_once_with(
        url="https://android.googlesource.com/platform/tools/adt/idea/"
        "+archive/refs/heads/mirror-goog-studio-master-dev/"
        "artwork/resources/device-art-resources/pixel_3a.tar.gz",
        download_path=mock_sdk.root_path,
    )

    # An attempt to unpack the skin was made.
    mock_sdk.command.shutil.unpack_archive.assert_called_once_with(
        skin_tgz_path, extract_dir=mock_sdk.root_path / "skins" / "pixel_3a"
    )

    # Original file wasn't deleted.
    assert skin_tgz_path.unlink.call_count == 0


def test_default_name(mock_sdk, tmp_path):
    """A new emulator can be created with the default name."""
    # This test doesn't validate most of the test process;
    # it only checks that the emulator is created with the default name.

    # User provides no input; default name will be used
    mock_sdk.command.input.return_value = ""

    # Mock the initial output of an AVD config file.
    avd_config_path = tmp_path / ".android" / "avd" / "beePhone.avd" / "config.ini"
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w") as f:
        f.write("hw.device.name=pixel\n")

    # Consider to remove if block when we drop py3.7 support.
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    if sys.version_info < (3, 8):
        skin_tgz_path = FsPathMock("")
        mock_sdk.command.download_url.return_value = skin_tgz_path

    # Create the emulator
    avd = mock_sdk.create_emulator()

    # The expected device AVD was created.
    assert avd == "beePhone"


def test_default_name_with_collisions(mock_sdk, tmp_path):
    """The default name will avoid collisions with existing emulators."""
    # This test doesn't validate most of the test process;
    # it only checks that the emulator is created with the default name.

    # Create some existing emulators that will collide with the default name.
    mock_sdk.emulators = MagicMock(
        return_value=[
            "beePhone2",
            "runningEmulator",
            "beePhone",
        ]
    )
    # User provides no input; default name will be used
    mock_sdk.command.input.return_value = ""

    # Mock the initial output of an AVD config file.
    avd_config_path = tmp_path / ".android" / "avd" / "beePhone3.avd" / "config.ini"
    avd_config_path.parent.mkdir(parents=True)
    with avd_config_path.open("w") as f:
        f.write("hw.device.name=pixel\n")

    # Consider to remove if block when we drop py3.7 support.
    # MagicMock below py3.8 doesn't has __fspath__ attribute.
    if sys.version_info < (3, 8):
        skin_tgz_path = FsPathMock("")
        mock_sdk.command.download_url.return_value = skin_tgz_path

    # Create the emulator
    avd = mock_sdk.create_emulator()

    # The expected device AVD was created.
    assert avd == "beePhone3"
