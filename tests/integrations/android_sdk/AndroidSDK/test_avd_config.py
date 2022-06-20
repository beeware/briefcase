import pytest


@pytest.fixture
def test_device(tmp_path):
    """Create an AVD configuration file."""
    config_file = tmp_path / ".android" / "avd" / "testDevice.avd" / "config.ini"
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

    return config_file


def test_avd_config(mock_sdk, test_device):
    """An AVD configuration can be read."""
    assert mock_sdk.avd_config("testDevice") == {
        "avd.ini.encoding": "UTF-8",
        "hw.device.manufacturer": "Google",
        "hw.device.name": "pixel",
        "weird.key": "good=bad",
        "PlayStore.enabled": "no",
        "avd.name": "testDevice",
        "disk.cachePartition": "yes",
        "disk.cachePartition.size": "37MB",
    }
