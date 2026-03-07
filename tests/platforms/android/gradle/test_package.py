import argparse


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


def test_add_options(package_command):
    """add_options registers --identity, --keystore-alias, --keystore-password, and
    --key-password."""
    parser = argparse.ArgumentParser()
    package_command.add_options(parser)

    args = parser.parse_args(
        [
            "--identity",
            "/path/to/my.jks",
            "--keystore-alias",
            "mykey",
            "--keystore-password",
            "storepass",
            "--key-password",
            "keypass",
        ]
    )

    assert args.identity == "/path/to/my.jks"
    assert args.keystore_alias == "mykey"
    assert args.keystore_password == "storepass"
    assert args.key_password == "keypass"


def test_add_options_defaults(package_command):
    """All new signing options default to None when not supplied."""
    parser = argparse.ArgumentParser()
    package_command.add_options(parser)

    args = parser.parse_args([])

    assert args.identity is None
    assert args.keystore_alias is None
    assert args.keystore_password is None
    assert args.key_password is None
