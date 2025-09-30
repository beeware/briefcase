# tests/commands/config/test_validation.py
import pytest

from briefcase.commands.config import normalize_key, validate_key
from briefcase.exceptions import BriefcaseConfigError


@pytest.mark.parametrize(
    "email",
    [
        "user@example.com",
        "first.last+tag@sub.domain.co",
        "u@d.gr",
    ],
)
def test_author_email_valid(email):
    """Valid email formats pass."""
    validate_key("author.email", email)


@pytest.mark.parametrize(
    "email",
    [
        "no-at-symbol",
        "user@",
        "@domain.com",
        "a@b",
        "   ",
        "",
    ],
)
def test_author_email_invalid(email):
    """Invalid email formats raise BriefcaseConfigError."""
    with pytest.raises(BriefcaseConfigError):
        validate_key("author.email", email)


@pytest.mark.parametrize(
    "name",
    [
        "Alice",
        "Bob Smith",
        "Dr. Charlie Q. Public, PhD",
    ],
)
def test_author_name_valid(name):
    """Non-empty author names pass."""
    validate_key("author.name", name)


@pytest.mark.parametrize("name", ["", "   "])
def test_author_name_invalid_empty(name):
    """Empty/whitespace author names are rejected."""
    with pytest.raises(BriefcaseConfigError):
        validate_key("author.name", name)


@pytest.mark.parametrize(
    "value",
    [
        "@Pixel_7_API_34",
        "@MyAVD",
        "emulator-5554",
        "emulator-1234",
    ],
)
def test_android_device_valid_patterns(value):
    """Accepted android device patterns (@AVD, emulator-####)."""
    validate_key("android.device", value)


@pytest.mark.parametrize(
    "value",
    [
        "R58N42ABCD",  # physical device serial -> invalid per current rules
        "pixel7",  # missing leading '@'
        "emulator-xyz",  # bad emulator suffix
        "emulator-",  # missing digits
        "",
        "   ",
    ],
)
def test_android_device_invalid_patterns(value):
    """Rejected android device patterns."""
    with pytest.raises(BriefcaseConfigError):
        validate_key("android.device", value)


@pytest.mark.parametrize(
    "value",
    [
        "00008020-001C111E0A88002E",  # UDID-like
        "C0FFEE00-0000-1111-2222-DEADBEEF0001",
        "Alice's iPhone::iOS 17.5",  # DeviceName::iOS X.Y
        "My Test Phone::iOS 16.0",
    ],
)
def test_ios_device_valid(value):
    """Accepted iOS device identifiers."""
    validate_key("iOS.device", value)


@pytest.mark.parametrize(
    "value",
    [
        "iPhone",  # no ::iOS X.Y and not UDID
        "iPhone::17.5",  # missing 'iOS ' prefix
        "iPhone::iOS",  # missing version
        "",
        "   ",
    ],
)
def test_ios_device_invalid(value):
    """Rejected iOS device identifiers."""
    with pytest.raises(BriefcaseConfigError):
        validate_key("iOS.device", value)


@pytest.mark.parametrize(
    "key",
    [
        "android.device",
        "iOS.device",
    ],
)
def test_question_sentinel_allowed_for_devices_and_identity(key):
    """'?' is accepted for device/identity keys to force interactive selection."""
    validate_key(key, "?")


@pytest.mark.parametrize(
    "key",
    [
        "author.name",
        "author.email",
    ],
)
def test_question_sentinel_rejected_for_other_keys(key):
    """'?' on non-device/identity keys is rejected."""
    with pytest.raises(BriefcaseConfigError):
        validate_key(key, "?")


@pytest.mark.parametrize(
    "key,value",
    [
        (
            "ios.device",
            "00008020-001C111E0A88002E",
        ),
        ("foo.bar", "baz"),
    ],
)
def test_unknown_keys_rejected(key, value):
    """Keys outside the strict allow-list are rejected."""
    with pytest.raises(BriefcaseConfigError):
        validate_key(key, value)


def test_normalize_key_trims_only():
    # preserves case; trims whitespace
    assert normalize_key("  iOS.device  ") == "iOS.device"
    assert normalize_key("") == ""
    assert normalize_key(None) == ""
