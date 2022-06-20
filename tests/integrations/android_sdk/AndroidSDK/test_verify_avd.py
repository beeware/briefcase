import os
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_missing_avd_config(mock_sdk):
    """If an AVD config can't be found, raise an error."""
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to read configuration of AVD @unknownDevice",
    ):
        mock_sdk.verify_avd("unknownDevice")


def test_incomplete_avd_config(mock_sdk, capsys):
    """If the AVD config doesn't contain an image.sysdir.1 key, raise a
    warning, but continue."""
    # Mock an AVD configuration that doesn't contain an image.sysdir.1 key
    mock_sdk.avd_config = mock.MagicMock(
        return_value={
            "avd.ini.encoding": "UTF-8",
            "hw.device.manufacturer": "Google",
            "hw.device.name": "pixel",
            "weird.key": "good=bad",
            "PlayStore.enabled": "no",
            "avd.name": "beePhone",
            "disk.cachePartition": "yes",
            "disk.cachePartition.size": "42M",
        }
    )
    mock_sdk.verify_system_image = mock.MagicMock()

    # Verify the AVD
    mock_sdk.verify_avd("incompleteDevice")

    # The AVD config was loaded.
    mock_sdk.avd_config.assert_called_with("incompleteDevice")

    # A warning message was output
    assert "WARNING: Unable to read AVD configuration" in capsys.readouterr().out

    # The system image was not verified
    mock_sdk.verify_system_image.assert_not_called()


def test_valid_avd_config(mock_sdk):
    """If the AVD config contains an image.sysdir.1 key, it is used to create a
    system image name."""
    # Mock an AVD configuration that contains an image.sysdir.1 key
    mock_sdk.avd_config = mock.MagicMock(
        return_value={
            "avd.ini.encoding": "UTF-8",
            "hw.device.manufacturer": "Google",
            "hw.device.name": "pixel",
            "weird.key": "good=bad",
            "PlayStore.enabled": "no",
            "avd.name": "beePhone",
            "disk.cachePartition": "yes",
            "disk.cachePartition.size": "42M",
            # Create an OS-dependent image.sysdir.1 value, with a trailing slash.
            "image.sysdir.1": os.fsdecode(
                Path("system-images") / "android-31" / "default" / "arm64-v8a"
            )
            + "/",
        }
    )
    mock_sdk.verify_system_image = mock.MagicMock()

    # Verify the AVD
    mock_sdk.verify_avd("goodDevice")

    # The AVD config was loaded.
    mock_sdk.avd_config.assert_called_with("goodDevice")

    # The system image was not verified
    mock_sdk.verify_system_image.assert_called_once_with(
        "system-images;android-31;default;arm64-v8a"
    )
