def test_adhoc_sign_help(package_command):
    """The adhoc sign help text is overridden for Linux."""
    assert package_command.ADHOC_SIGN_HELP == (
        "Perform no signing on the package. If signing is not performed, "
        "users will not be able to verify the provenance of the package."
    )


def test_identity_help(package_command):
    """The identity help text is overridden for Linux."""
    assert package_command.IDENTITY_HELP == (
        "The GPG signing identity to use to sign the package. This can be the "
        "fingerprint, key ID, or the name/email address of any GPG identity "
        "available on the system."
    )
