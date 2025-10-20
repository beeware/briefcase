import pytest


def test_author_email_valid(cfg_mod):
    cfg_mod.validate_key("author.email", "first.last+tag@sub.domain.co")


@pytest.mark.parametrize("bad", ["no-at", "a@b", "", "   "])
def test_author_email_invalid(cfg_mod, bad):
    with pytest.raises(cfg_mod.BriefcaseConfigError):
        cfg_mod.validate_key("author.email", bad)


def test_android_device_valid(cfg_mod):
    for v in ["@Pixel_7_API_34", "emulator-5554"]:
        cfg_mod.validate_key("android.device", v)


@pytest.mark.parametrize("bad", ["emu-xyz", "pixel7", "", "   "])
def test_android_device_invalid(cfg_mod, bad):
    with pytest.raises(cfg_mod.BriefcaseConfigError):
        cfg_mod.validate_key("android.device", bad)


def test_ios_device_valid(cfg_mod):
    for v in ["00008020-001C111E0A88002E", "My iPhone::iOS 17.4"]:
        cfg_mod.validate_key("iOS.device", v)


@pytest.mark.parametrize("bad", ["iPhone", "iPhone::17.4", "", "   "])
def test_ios_device_invalid(cfg_mod, bad):
    with pytest.raises(cfg_mod.BriefcaseConfigError):
        cfg_mod.validate_key("iOS.device", bad)


def test_question_sentinel_only_for_devices(cfg_mod):
    for k in ["android.device", "iOS.device"]:
        cfg_mod.validate_key(k, "?")
    with pytest.raises(cfg_mod.BriefcaseConfigError):
        cfg_mod.validate_key("author.name", "?")
