from unittest.mock import MagicMock

from briefcase.integrations.android_sdk import ANDROID_MIN_OS_VERSION, min_api_level


def test_min_api_level_int():
    """min_api_level returns the app's min_os_version when configured as an int."""
    app = MagicMock()
    app.min_os_version = 28
    assert min_api_level(app) == 28


def test_min_api_level_str():
    """min_api_level coerces min_os_version to int when configured as a string."""
    app = MagicMock()
    app.min_os_version = "28"
    assert min_api_level(app) == 28


def test_min_api_level_default():
    """min_api_level falls back to ANDROID_MIN_OS_VERSION when min_os_version is not
    set."""
    app = MagicMock()
    del app.min_os_version
    assert min_api_level(app) == ANDROID_MIN_OS_VERSION
