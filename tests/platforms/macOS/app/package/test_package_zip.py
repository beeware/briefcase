from zipfile import ZipFile


def test_package_zip(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
):
    """A macOS App can be packaged as a zip."""
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
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "First App.app",
        identity=sekrit_identity,
    )

    # No dmg was built.
    assert package_command.dmgbuild.build_dmg.call_count == 0

    # If the DMG doesn't exist, it can't be signed either.
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    assert package_command.sign_file.call_count == 0

    # The packaged archive exists, and contains all the files,
    # contained in the `.app` bundle.
    archive_file = tmp_path / "base_path/dist/First App-0.0.1.app.zip"
    assert archive_file.exists()
    with ZipFile(archive_file) as archive:
        assert sorted(archive.namelist()) == [
            "First App.app/",
            "First App.app/Contents/",
            "First App.app/Contents/Frameworks/",
            "First App.app/Contents/Frameworks/Extras.framework/",
            "First App.app/Contents/Frameworks/Extras.framework/Resources/",
            "First App.app/Contents/Frameworks/Extras.framework/Resources/extras.dylib",
            "First App.app/Contents/Info.plist",
            "First App.app/Contents/MacOS/",
            "First App.app/Contents/MacOS/First App",
            "First App.app/Contents/Resources/",
            "First App.app/Contents/Resources/app_packages/",
            "First App.app/Contents/Resources/app_packages/Extras.app/",
            "First App.app/Contents/Resources/app_packages/Extras.app/Contents/",
            "First App.app/Contents/Resources/app_packages/Extras.app/Contents/MacOS/",
            "First App.app/Contents/Resources/app_packages/Extras.app/Contents/MacOS/Extras",
            "First App.app/Contents/Resources/app_packages/first.other",
            "First App.app/Contents/Resources/app_packages/first_dylib.dylib",
            "First App.app/Contents/Resources/app_packages/first_so.so",
            "First App.app/Contents/Resources/app_packages/first_symlink.so",
            "First App.app/Contents/Resources/app_packages/other_binary",
            "First App.app/Contents/Resources/app_packages/second.other",
            "First App.app/Contents/Resources/app_packages/special.binary",
            "First App.app/Contents/Resources/app_packages/subfolder/",
            "First App.app/Contents/Resources/app_packages/subfolder/second_dylib.dylib",
            "First App.app/Contents/Resources/app_packages/subfolder/second_so.so",
            "First App.app/Contents/Resources/app_packages/unknown.binary",
        ]


def test_zip_no_notarization(package_command, sekrit_identity, first_app_with_binaries):
    """A macOS App can be packaged as a zip, without notarization."""
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
