from unittest.mock import MagicMock


def test_package_zip(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
):
    """A macOS App can be packaged as a zip."""
    # Mock the creation of the ditto archive
    package_command.ditto_archive = MagicMock()

    # Select zip packaging
    first_app_with_binaries.packaging_format = "zip"

    # Select a code signing identity
    package_command.select_identity.return_value = sekrit_identity

    # Package the app in zip (not DMG) format
    package_command.package_app(first_app_with_binaries)

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=sekrit_identity,
    )

    # A request has been made to notarize the app
    package_command.notarize.assert_called_once_with(
        first_app_with_binaries,
        identity=sekrit_identity,
    )

    # No dmg was built.
    assert package_command.dmgbuild.build_dmg.call_count == 0

    # If the DMG doesn't exist, it can't be signed either.
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    assert package_command.sign_file.call_count == 0

    # The notarization process will create the final artefact;
    # since we're mocking notarize, we rely on the notarization tests
    # to verify that the final distribution artefact was created.


def test_zip_no_notarization(
    package_command,
    sekrit_identity,
    first_app_with_binaries,
    tmp_path,
):
    """A macOS App can be packaged as a zip, without notarization."""
    # Mock the creation of the ditto archive
    package_command.ditto_archive = MagicMock()

    # Select zip packaging
    first_app_with_binaries.packaging_format = "zip"

    # Select a code signing identity
    package_command.select_identity.return_value = sekrit_identity

    # Package the app in zip (not DMG) format, disabling notarization
    package_command.package_app(
        first_app_with_binaries,
        notarize_app=False,
    )

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=sekrit_identity,
    )

    # No request has been made to notarize the app
    package_command.notarize.assert_not_called()

    # No dmg was built.
    assert package_command.dmgbuild.build_dmg.call_count == 0

    # If the DMG doesn't exist, it can't be signed either.
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    assert package_command.sign_file.call_count == 0

    # Since we're not notarizing, the packaged archive was created.
    package_command.ditto_archive.assert_called_once_with(
        tmp_path / "base_path/build/first-app/macos/app/First App.app",
        tmp_path / "base_path/dist/First App-0.0.1.app.zip",
    )
