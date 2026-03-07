def test_packaging_formats(package_command):
    assert package_command.packaging_formats == ["aab", "apk", "debug-apk"]


def test_default_packaging_format(package_command):
    assert package_command.default_packaging_format == "aab"


def test_adhoc_sign_help(package_command):
    """ADHOC_SIGN_HELP is overridden from the base class placeholder."""
    assert package_command.ADHOC_SIGN_HELP != "Ignored; signing is not supported"
    assert "unsigned" in package_command.ADHOC_SIGN_HELP.lower()


def test_identity_help(package_command):
    """IDENTITY_HELP is overridden from the base class placeholder."""
    assert package_command.IDENTITY_HELP != "Ignored; signing is not supported"
    assert "keystore" in package_command.IDENTITY_HELP.lower()
