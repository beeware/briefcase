import pytest

from ....utils import create_file


@pytest.fixture(params=["testDevice.avd", "originalDevice.avd"])
def test_device(tmp_path, request):
    """Create an AVD configuration file."""
    avd_path = tmp_path / "home/.android/avd"
    config_file = avd_path / request.param / "config.ini"
    config_file.parent.mkdir(parents=True)
    create_file(avd_path / "testDevice.ini", f"path={config_file.parent}\n")

    # Write a default config. It contains:
    # * blank lines
    # * a key whose value explicitly contains an equals sign.
    with config_file.open("w", encoding="utf-8") as f:
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

    with test_device.open(encoding="utf-8") as f:
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

    with test_device.open(encoding="utf-8") as f:
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


def test_update_relative_path(android_sdk, tmp_path):
    """Updates go to the same directory that the emulator selects for reading."""
    relative_config = create_file(
        android_sdk.avd_path / "originalDevice.avd/config.ini",
        "hw.device.name=pixel\n",
    )
    absolute_config = create_file(
        tmp_path / "anotherDevice.avd/config.ini",
        "hw.device.name=slab\n",
    )
    create_file(
        android_sdk.avd_path / "testDevice.ini",
        f"path={absolute_config.parent}\npath.rel=avd/originalDevice.avd\n",
    )

    android_sdk.update_emulator_config("testDevice", {"hw.keyboard": "yes"})

    assert relative_config.read_text(encoding="utf-8") == (
        "hw.device.name=pixel\nhw.keyboard=yes\n"
    )
    assert absolute_config.read_text(encoding="utf-8") == "hw.device.name=slab\n"
