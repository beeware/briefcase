def test_avd_config(mock_tools, android_sdk, tmp_path):
    """An AVD configuration can be read."""
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
    config_file = (
        tmp_path / "home" / ".android" / "avd" / "testDevice.avd" / "config.ini"
    )
    config_file.parent.mkdir(parents=True)

    # Write a default config. It contains:
    # * blank lines
    # * a key whose value explicitly contains an equals sign.
    # * spaces either side of the key/value separator
    with config_file.open("w") as f:
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
