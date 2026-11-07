import pytest

from briefcase.exceptions import BriefcaseCommandError

from ....utils import create_file


@pytest.mark.parametrize(
    "directory",
    ["testDevice.avd", "originalDevice.avd", "device with spaces=é.avd"],
)
def test_avd_config(mock_tools, android_sdk, tmp_path, directory):
    """An AVD configuration can be read even after the device is renamed."""
    config_file = android_sdk.avd_path / directory / "config.ini"
    config_file.parent.mkdir(parents=True)
    create_file(
        android_sdk.avd_path / "testDevice.ini",
        f"avd.ini.encoding=UTF-8\npath={config_file.parent}\n",
    )

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
avd.name=testDevice
disk.cachePartition=yes
disk.cachePartition.size=37MB
"""
        )

    assert android_sdk.avd_config("testDevice") == {
        "avd.ini.encoding": "UTF-8",
        "hw.device.manufacturer": "Google",
        "hw.device.name": "pixel",
        "weird.key": "good=bad",
        "PlayStore.enabled": "no",
        "avd.name": "testDevice",
        "disk.cachePartition": "yes",
        "disk.cachePartition.size": "37MB",
    }


def test_avd_config_with_space(mock_tools, android_sdk, tmp_path):
    """An AVD configuration that contains spaces can be read."""
    config_file = tmp_path / "home/.android/avd/testDevice.avd/config.ini"
    config_file.parent.mkdir(parents=True)
    create_file(
        android_sdk.avd_path / "testDevice.ini",
        f"\navd.ini.encoding = UTF-8\npath = {config_file.parent}\n",
    )

    # Write a default config. It contains:
    # * blank lines
    # * a key whose value explicitly contains an equals sign.
    # * spaces either side of the key/value separator
    with config_file.open("w", encoding="utf-8") as f:
        f.write(
            """
avd.ini.encoding = UTF-8
hw.device.manufacturer = Google
hw.device.name = pixel
weird.key = good=bad

PlayStore.enabled = no
avd.name = testDevice
disk.cachePartition = yes
disk.cachePartition.size = 37MB
"""
        )

    assert android_sdk.avd_config("testDevice") == {
        "avd.ini.encoding": "UTF-8",
        "hw.device.manufacturer": "Google",
        "hw.device.name": "pixel",
        "weird.key": "good=bad",
        "PlayStore.enabled": "no",
        "avd.name": "testDevice",
        "disk.cachePartition": "yes",
        "disk.cachePartition.size": "37MB",
    }


@pytest.mark.parametrize("metadata", [None, "", "path=\n", "path.rel=\n"])
def test_missing_avd_path(android_sdk, metadata):
    """A directory alone is not sufficient to identify an AVD."""
    create_file(
        android_sdk.avd_path / "testDevice.avd/config.ini",
        "hw.device.name=pixel\n",
    )
    if metadata is not None:
        create_file(android_sdk.avd_path / "testDevice.ini", metadata)

    with pytest.raises(
        BriefcaseCommandError,
        match="Unable to read configuration of AVD @testDevice",
    ):
        android_sdk.avd_config("testDevice")


@pytest.mark.parametrize("relative_path", [None, "avd/missingDevice.avd"])
def test_missing_config(android_sdk, tmp_path, relative_path):
    """An unreadable referenced AVD configuration raises a useful error."""
    metadata = f"path={tmp_path / 'missingDevice.avd'}\n"
    if relative_path is not None:
        metadata += f"path.rel={relative_path}\n"
    create_file(android_sdk.avd_path / "testDevice.ini", metadata)

    with pytest.raises(
        BriefcaseCommandError,
        match="Unable to read configuration of AVD @testDevice",
    ):
        android_sdk.avd_config("testDevice")


@pytest.mark.parametrize("absolute_path_exists", [True, False])
def test_relative_path_preferred(android_sdk, tmp_path, absolute_path_exists):
    """The relative path takes precedence over an absolute path, like the emulator."""
    absolute_path = tmp_path / "custom AVD location=é"
    if absolute_path_exists:
        create_file(absolute_path / "config.ini", "hw.device.name=pixel\n")
    create_file(
        android_sdk.avd_path / "originalDevice.avd/config.ini",
        "hw.device.name=slab\n",
    )
    create_file(
        android_sdk.avd_path / "testDevice.ini",
        f"path={absolute_path}\npath.rel=avd/originalDevice.avd\n",
    )

    assert android_sdk.avd_config("testDevice") == {"hw.device.name": "slab"}


def test_absolute_path_fallback(android_sdk, tmp_path):
    """The absolute path is used if the relative directory is missing."""
    absolute_path = tmp_path / "custom AVD location=é"
    create_file(absolute_path / "config.ini", "hw.device.name=pixel\n")
    create_file(
        android_sdk.avd_path / "testDevice.ini",
        f"path={absolute_path}\npath.rel=avd/missingDevice.avd\n",
    )

    assert android_sdk.avd_config("testDevice") == {"hw.device.name": "pixel"}


def test_relative_path_only(android_sdk):
    """A valid relative path does not require an absolute path."""
    create_file(
        android_sdk.avd_path / "originalDevice.avd/config.ini",
        "hw.device.name=slab\n",
    )
    create_file(
        android_sdk.avd_path / "testDevice.ini",
        "path.rel=avd/originalDevice.avd\n",
    )

    assert android_sdk.avd_config("testDevice") == {"hw.device.name": "slab"}
