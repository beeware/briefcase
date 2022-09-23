import pytest


@pytest.fixture
def test_device(tmp_path):
    """Create an AVD configuration file."""
    config_file = (
        tmp_path / "home" / ".android" / "avd" / "testDevice.avd" / "config.ini"
    )
    config_file.parent.mkdir(parents=True)

    # Write a default config. It contains:
    # * blank lines
    # * a key whose value explicitly contains an equals sign.
    with config_file.open("w") as f:
        f.write(
            """
avd.ini.encoding=UTF-8
hw.device.manufacturer=Google
hw.device.name=pixel
weird.key=good=bad

PlayStore.enabled=no
avd.name=beePhone
disk.cachePartition=yes
disk.cachePartition.size=42M
"""
        )

    return config_file


def test_update_existing(android_sdk, test_device):
    """Existing keys in an Android AVD config can be updated."""
    # Update 2 keys in the config
    android_sdk.update_emulator_config(
        "testDevice",
        {
            "avd.name": "testDevice",
            "disk.cachePartition.size": "37MB",
        },
    )

    with test_device.open() as f:
        content = f.read()

    # Keys have been updated, order is preserved.
    assert (
        content
        == """avd.ini.encoding=UTF-8
hw.device.manufacturer=Google
hw.device.name=pixel
weird.key=good=bad
PlayStore.enabled=no
avd.name=testDevice
disk.cachePartition=yes
disk.cachePartition.size=37MB
"""
    )


def test_new_content(android_sdk, test_device):
    """New keys can be added to an Android AVD config."""
    # Add 2 new keys to the config
    android_sdk.update_emulator_config(
        "testDevice",
        {
            "skin.name": "pixel_3a",
            "skin.path": "skins/pixel_3a",
        },
    )

    with test_device.open() as f:
        content = f.read()

    # New keys are appended to the end of the file
    # Newlines have been dropped
    assert (
        content
        == """avd.ini.encoding=UTF-8
hw.device.manufacturer=Google
hw.device.name=pixel
weird.key=good=bad
PlayStore.enabled=no
avd.name=beePhone
disk.cachePartition=yes
disk.cachePartition.size=42M
skin.name=pixel_3a
skin.path=skins/pixel_3a
"""
    )
