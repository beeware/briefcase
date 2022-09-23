import os
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_missing_avd_config(android_sdk):
    """If an AVD config can't be found, raise an error."""
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to read configuration of AVD @unknownDevice",
    ):
        android_sdk.verify_avd("unknownDevice")


def test_minimal_config(android_sdk, capsys):
    """If the AVD config doesn't contain any interesting keys, raise a warning,
    but continue."""
    # Mock an AVD configuration that doesn't contain an image.sysdir.1,
    # skin.name or skin.path key.
    android_sdk.avd_config = mock.MagicMock(
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
    android_sdk.verify_system_image = mock.MagicMock()
    android_sdk.verify_emulator_skin = mock.MagicMock()

    # Verify the AVD
    android_sdk.verify_avd("minimalDevice")

    # The AVD config was loaded.
    android_sdk.avd_config.assert_called_with("minimalDevice")

    # A warning message was output
    assert "WARNING: Unable to determine AVD system image" in capsys.readouterr().out

    # The system image was not verified
    android_sdk.verify_system_image.assert_not_called()

    # An emulator skin was not verified
    android_sdk.verify_emulator_skin.assert_not_called()


def test_valid_system_image(android_sdk):
    """If the AVD config contains an image.sysdir.1 key, it is used to create a
    system image name."""
    # Mock an AVD configuration that contains an image.sysdir.1 key
    android_sdk.avd_config = mock.MagicMock(
        return_value={
            "avd.ini.encoding": "UTF-8",
            "hw.device.manufacturer": "Google",
            "hw.device.name": "pixel",
            "weird.key": "good=bad",
            "PlayStore.enabled": "no",
            "avd.name": "beePhone",
            "disk.cachePartition": "yes",
            "disk.cachePartition.size": "42M",
            # Add an OS-dependent image.sysdir.1 value, with a trailing slash.
            "image.sysdir.1": os.fsdecode(
                Path("system-images") / "android-31" / "default" / "arm64-v8a"
            )
            + "/",
        }
    )
    android_sdk.verify_system_image = mock.MagicMock()
    android_sdk.verify_emulator_skin = mock.MagicMock()

    # Verify the AVD
    android_sdk.verify_avd("goodDevice")

    # The AVD config was loaded.
    android_sdk.avd_config.assert_called_with("goodDevice")

    # The system image was not verified
    android_sdk.verify_system_image.assert_called_once_with(
        "system-images;android-31;default;arm64-v8a"
    )

    # The emulator skin was not verified
    android_sdk.verify_emulator_skin.assert_not_called()


def test_valid_emulator_skin(android_sdk):
    """If the AVD config contains a known emulator skin type, it is
    verified."""
    # Mock an AVD configuration that contains skin.name and skin.path keys
    android_sdk.avd_config = mock.MagicMock(
        return_value={
            "avd.ini.encoding": "UTF-8",
            "hw.device.manufacturer": "Google",
            "hw.device.name": "pixel",
            "weird.key": "good=bad",
            "PlayStore.enabled": "no",
            "avd.name": "beePhone",
            "disk.cachePartition": "yes",
            "disk.cachePartition.size": "42M",
            # Add an emulator skin.
            "skin.name": "pixel_3a",
            "skin.path": "skins/pixel_3a",
        }
    )
    android_sdk.verify_system_image = mock.MagicMock()
    android_sdk.verify_emulator_skin = mock.MagicMock()

    # Verify the AVD
    android_sdk.verify_avd("goodDevice")

    # The AVD config was loaded.
    android_sdk.avd_config.assert_called_with("goodDevice")

    # The system image was not verified
    android_sdk.verify_system_image.assert_not_called()

    # The emulator skin will be verified
    android_sdk.verify_emulator_skin.assert_called_with("pixel_3a")


def test_unrecognized_emulator_skin(android_sdk, capsys):
    """If the AVD config contains an emulator skin in an unusual location,
    raise a warning, but continue."""
    # Mock an AVD configuration that contains a skin.name and skin.path
    # in an unexpected location
    android_sdk.avd_config = mock.MagicMock(
        return_value={
            "avd.ini.encoding": "UTF-8",
            "hw.device.manufacturer": "Google",
            "hw.device.name": "pixel",
            "weird.key": "good=bad",
            "PlayStore.enabled": "no",
            "avd.name": "beePhone",
            "disk.cachePartition": "yes",
            "disk.cachePartition.size": "42M",
            # Add an emulator skin.
            "skin.name": "pixel_3a",
            "skin.path": "weird/pixel_3a",
        }
    )
    android_sdk.verify_system_image = mock.MagicMock()
    android_sdk.verify_emulator_skin = mock.MagicMock()

    # Verify the AVD
    android_sdk.verify_avd("goodDevice")

    # The AVD config was loaded.
    android_sdk.avd_config.assert_called_with("goodDevice")

    # A warning message was output
    assert "WARNING: Unrecognized device skin" in capsys.readouterr().out

    # The system image was not verified
    android_sdk.verify_system_image.assert_not_called()

    # The emulator skin was not verified
    android_sdk.verify_emulator_skin.assert_not_called()
