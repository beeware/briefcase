import plistlib
from unittest import mock

from .....utils import create_file


def test_gui_app(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    sekrit_installer_identity,
    tmp_path,
):
    """A macOS GUI app can be packaged as a .pkg installer."""
    first_app_with_binaries.packaging_format = "pkg"

    # Select a codesigning identity
    package_command.select_identity.side_effect = [
        sekrit_identity,
        sekrit_installer_identity,
    ]

    # Mock the notarization process
    package_command.notarize = mock.Mock()

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    # Create a pre-existing app bundle.
    create_file(
        bundle_path / "installer/root/First App.app/original",
        "Original app",
    )

    # Create a pre-existing package bundle.
    create_file(
        bundle_path / "installer/packages/first-app.pkg",
        "Original package",
    )

    # Create a pre-existing LICENSE
    create_file(
        bundle_path / "installer/resources/LICENSE",
        "Original License",
    )

    # Re-package the app
    package_command.package_app(first_app_with_binaries)

    # Two signing identities were selected; the second is an installer identity
    assert package_command.select_identity.mock_calls == [
        mock.call(identity=None),
        mock.call(identity=None, app_identity=sekrit_identity),
    ]

    # The app has been signed
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=sekrit_identity,
    )

    # App content has been copied into place.
    assert (bundle_path / "installer/root/First App.app/Contents/Info.plist").is_file()

    # When duplicating the app, symlinks have been preserved
    assert (
        bundle_path
        / "installer/root/First App.app/Contents/Frameworks/Extras.framework/Extras"
    ).is_symlink()

    # The license has been updated.
    assert (bundle_path / "installer/resources/LICENSE").read_text(
        encoding="utf-8"
    ) == "The Actual First App License"

    # The component list has been updated.
    with (bundle_path / "installer/components.plist").open("rb") as f:
        components = plistlib.load(f)

        assert components == [
            {
                "BundleHasStrictIdentifier": True,
                "BundleIsRelocatable": False,
                "BundleIsVersionChecked": True,
                "BundleOverwriteAction": "upgrade",
                "RootRelativeBundlePath": "First App.app",
            }
        ]

    assert package_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                "pkgbuild",
                "--root",
                bundle_path / "installer/root",
                "--component-plist",
                bundle_path / "installer/components.plist",
                "--install-location",
                "/Applications",
                bundle_path / "installer/packages/first-app.pkg",
            ],
            check=True,
        ),
        mock.call(
            [
                "productbuild",
                "--distribution",
                bundle_path / "installer/Distribution.xml",
                "--package-path",
                bundle_path / "installer/packages",
                "--resources",
                bundle_path / "installer/resources",
                "--sign",
                "CAFEFACE",
                tmp_path / "base_path/dist/First App-0.0.1.pkg",
            ],
            check=True,
        ),
    ]

    # Notarization was performed with the installer identity
    package_command.notarize.assert_called_once_with(
        first_app_with_binaries,
        identity=sekrit_identity,
        installer_identity=sekrit_installer_identity,
    )


def test_gui_app_adhoc_identity(
    package_command,
    first_app_with_binaries,
    adhoc_identity,
    tmp_path,
):
    """A macOS GUI app can be packaged as a .pkg installer."""
    first_app_with_binaries.packaging_format = "pkg"

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    # Mock the notarization process
    package_command.notarize = mock.Mock()

    # Create a pre-existing app bundle.
    create_file(
        bundle_path / "installer/root/First App.app/original",
        "Original app",
    )

    # Create a pre-existing package bundle.
    create_file(
        bundle_path / "installer/packages/first-app.pkg",
        "Original package",
    )

    # Create a pre-existing LICENSE
    create_file(
        bundle_path / "installer/resources/LICENSE",
        "Original License",
    )

    # Re-package the app
    package_command.package_app(
        first_app_with_binaries,
        adhoc_sign=True,
    )

    # The app has been signed
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=adhoc_identity,
    )

    # App content has been copied into place.
    assert (bundle_path / "installer/root/First App.app/Contents/Info.plist").is_file()

    # The license has been updated.
    assert (bundle_path / "installer/resources/LICENSE").read_text(
        encoding="utf-8"
    ) == "The Actual First App License"

    # The component list has been updated.
    with (bundle_path / "installer/components.plist").open("rb") as f:
        components = plistlib.load(f)

        assert components == [
            {
                "BundleHasStrictIdentifier": True,
                "BundleIsRelocatable": False,
                "BundleIsVersionChecked": True,
                "BundleOverwriteAction": "upgrade",
                "RootRelativeBundlePath": "First App.app",
            }
        ]

    assert package_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                "pkgbuild",
                "--root",
                bundle_path / "installer/root",
                "--component-plist",
                bundle_path / "installer/components.plist",
                "--install-location",
                "/Applications",
                bundle_path / "installer/packages/first-app.pkg",
            ],
            check=True,
        ),
        mock.call(
            [
                "productbuild",
                "--distribution",
                bundle_path / "installer/Distribution.xml",
                "--package-path",
                bundle_path / "installer/packages",
                "--resources",
                bundle_path / "installer/resources",
                tmp_path / "base_path/dist/First App-0.0.1.pkg",
            ],
            check=True,
        ),
    ]

    # No notarization was performed
    package_command.notarize.assert_not_called()


def test_console_app(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    sekrit_installer_identity,
    tmp_path,
):
    """A macOS console app can be packaged as a .pkg installer."""
    first_app_with_binaries.packaging_format = "pkg"
    first_app_with_binaries.console_app = True

    # Select a codesigning identity
    package_command.select_identity.side_effect = [
        sekrit_identity,
        sekrit_installer_identity,
    ]

    # Mock the notarization process
    package_command.notarize = mock.Mock()

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    # Package the app
    package_command.package_app(first_app_with_binaries)

    # Two signing identities were selected; the second is an installer identity
    assert package_command.select_identity.mock_calls == [
        mock.call(identity=None),
        mock.call(identity=None, app_identity=sekrit_identity),
    ]

    # The app has been signed
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=sekrit_identity,
    )

    # App content has been copied into place.
    assert (bundle_path / "installer/root/First App.app/Contents/Info.plist").is_file()

    # The license has been installed
    assert (bundle_path / "installer/resources/LICENSE").read_text(
        encoding="utf-8"
    ) == "The Actual First App License"

    # The component list has been updated.
    with (bundle_path / "installer/components.plist").open("rb") as f:
        components = plistlib.load(f)

        assert components == [
            {
                "BundleHasStrictIdentifier": True,
                "BundleIsRelocatable": False,
                "BundleIsVersionChecked": True,
                "BundleOverwriteAction": "upgrade",
                "RootRelativeBundlePath": "First App.app",
            }
        ]

    assert package_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                "pkgbuild",
                "--root",
                bundle_path / "installer/root",
                "--component-plist",
                bundle_path / "installer/components.plist",
                "--install-location",
                "/Library/First App",
                "--scripts",
                bundle_path / "installer/scripts",
                bundle_path / "installer/packages/first-app.pkg",
            ],
            check=True,
        ),
        mock.call(
            [
                "productbuild",
                "--distribution",
                bundle_path / "installer/Distribution.xml",
                "--package-path",
                bundle_path / "installer/packages",
                "--resources",
                bundle_path / "installer/resources",
                "--sign",
                "CAFEFACE",
                tmp_path / "base_path/dist/First App-0.0.1.pkg",
            ],
            check=True,
        ),
    ]

    # Notarization was performed with the installer identity
    package_command.notarize.assert_called_once_with(
        first_app_with_binaries,
        identity=sekrit_identity,
        installer_identity=sekrit_installer_identity,
    )


def test_console_app_adhoc_signed(
    package_command,
    first_app_with_binaries,
    adhoc_identity,
    tmp_path,
):
    """A macOS console app can be packaged as a .pkg installer."""
    first_app_with_binaries.packaging_format = "pkg"
    first_app_with_binaries.console_app = True

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    # Mock the notarization process
    package_command.notarize = mock.Mock()

    # Package the app
    package_command.package_app(
        first_app_with_binaries,
        adhoc_sign=True,
    )

    # The app has been signed
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=adhoc_identity,
    )

    # App content has been copied into place.
    assert (bundle_path / "installer/root/First App.app/Contents/Info.plist").is_file()

    # The license has been installed
    assert (bundle_path / "installer/resources/LICENSE").read_text(
        encoding="utf-8"
    ) == "The Actual First App License"

    # The component list has been updated.
    with (bundle_path / "installer/components.plist").open("rb") as f:
        components = plistlib.load(f)

        assert components == [
            {
                "BundleHasStrictIdentifier": True,
                "BundleIsRelocatable": False,
                "BundleIsVersionChecked": True,
                "BundleOverwriteAction": "upgrade",
                "RootRelativeBundlePath": "First App.app",
            }
        ]

    assert package_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                "pkgbuild",
                "--root",
                bundle_path / "installer/root",
                "--component-plist",
                bundle_path / "installer/components.plist",
                "--install-location",
                "/Library/First App",
                "--scripts",
                bundle_path / "installer/scripts",
                bundle_path / "installer/packages/first-app.pkg",
            ],
            check=True,
        ),
        mock.call(
            [
                "productbuild",
                "--distribution",
                bundle_path / "installer/Distribution.xml",
                "--package-path",
                bundle_path / "installer/packages",
                "--resources",
                bundle_path / "installer/resources",
                tmp_path / "base_path/dist/First App-0.0.1.pkg",
            ],
            check=True,
        ),
    ]

    # No notarization was performed
    package_command.notarize.assert_not_called()


def test_no_license(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    sekrit_installer_identity,
    tmp_path,
):
    """If the project has no license file, an error is raised."""
    # Reset license files list
    first_app_with_binaries.license_files = []
    first_app_with_binaries.packaging_format = "pkg"

    # Select a codesigning identity
    package_command.select_identity.side_effect = [
        sekrit_identity,
        sekrit_installer_identity,
    ]

    # Mock the notarization process
    package_command.notarize = mock.Mock()

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    # Create a pre-existing app bundle.
    create_file(
        bundle_path / "installer/root/First App.app/original",
        "Original app",
    )

    # Create a pre-existing package bundle.
    create_file(
        bundle_path / "installer/packages/first-app.pkg",
        "Original package",
    )

    # Re-package the app
    package_command.package_app(first_app_with_binaries)

    # Two signing identities were selected; the second is an installer identity
    assert package_command.select_identity.mock_calls == [
        mock.call(identity=None),
        mock.call(identity=None, app_identity=sekrit_identity),
    ]

    # The app has been signed
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=sekrit_identity,
    )

    # App content has been copied into place.
    assert (bundle_path / "installer/root/First App.app/Contents/Info.plist").is_file()

    # When duplicating the app, symlinks have been preserved
    assert (
        bundle_path
        / "installer/root/First App.app/Contents/Frameworks/Extras.framework/Extras"
    ).is_symlink()

    # There are no license files in the resources directory
    assert list((bundle_path / "installer/resources").iterdir()) == []

    # The component list has been updated.
    with (bundle_path / "installer/components.plist").open("rb") as f:
        components = plistlib.load(f)

        assert components == [
            {
                "BundleHasStrictIdentifier": True,
                "BundleIsRelocatable": False,
                "BundleIsVersionChecked": True,
                "BundleOverwriteAction": "upgrade",
                "RootRelativeBundlePath": "First App.app",
            }
        ]

    assert package_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                "pkgbuild",
                "--root",
                bundle_path / "installer/root",
                "--component-plist",
                bundle_path / "installer/components.plist",
                "--install-location",
                "/Applications",
                bundle_path / "installer/packages/first-app.pkg",
            ],
            check=True,
        ),
        mock.call(
            [
                "productbuild",
                "--distribution",
                bundle_path / "installer/Distribution.xml",
                "--package-path",
                bundle_path / "installer/packages",
                "--resources",
                bundle_path / "installer/resources",
                "--sign",
                "CAFEFACE",
                tmp_path / "base_path/dist/First App-0.0.1.pkg",
            ],
            check=True,
        ),
    ]

    # Notarization was performed with the installer identity
    package_command.notarize.assert_called_once_with(
        first_app_with_binaries,
        identity=sekrit_identity,
        installer_identity=sekrit_installer_identity,
    )


def test_package_pkg_previously_built(
    package_command,
    first_app_with_binaries,
    adhoc_identity,
    tmp_path,
):
    """If a previous installer was built, the package folder is recreated."""
    first_app_with_binaries.packaging_format = "pkg"

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    # Create a pre-existing app bundle.
    create_file(
        bundle_path / "installer/root/First App.app/original",
        "Original app",
    )

    # Create a pre-existing package bundle.
    create_file(
        bundle_path / "installer/packages/first-app.pkg",
        "Original package",
    )

    # Create a pre-existing LICENSE
    create_file(
        bundle_path / "installer/resources/LICENSE",
        "Original License",
    )

    # Re-package the app
    package_command.package_app(
        first_app_with_binaries,
        adhoc_sign=True,
    )

    # The app has been signed
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=adhoc_identity,
    )

    # App content has been copied into place.
    assert (bundle_path / "installer/root/First App.app/Contents/Info.plist").is_file()

    # ... but the old file doesn't exist
    assert not (bundle_path / "installer/root/First App.app/original").exists()

    # The old package data doesn't exist either
    assert not (bundle_path / "installer/packages/first-app.pkg").exists()

    # The license has been updated.
    assert (bundle_path / "installer/resources/LICENSE").read_text(
        encoding="utf-8"
    ) == "The Actual First App License"

    # The component list has been updated.
    with (bundle_path / "installer/components.plist").open("rb") as f:
        components = plistlib.load(f)

        assert components == [
            {
                "BundleHasStrictIdentifier": True,
                "BundleIsRelocatable": False,
                "BundleIsVersionChecked": True,
                "BundleOverwriteAction": "upgrade",
                "RootRelativeBundlePath": "First App.app",
            }
        ]

    assert package_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                "pkgbuild",
                "--root",
                bundle_path / "installer/root",
                "--component-plist",
                bundle_path / "installer/components.plist",
                "--install-location",
                "/Applications",
                bundle_path / "installer/packages/first-app.pkg",
            ],
            check=True,
        ),
        mock.call(
            [
                "productbuild",
                "--distribution",
                bundle_path / "installer/Distribution.xml",
                "--package-path",
                bundle_path / "installer/packages",
                "--resources",
                bundle_path / "installer/resources",
                tmp_path / "base_path/dist/First App-0.0.1.pkg",
            ],
            check=True,
        ),
    ]


def test_external_app(
    package_command,
    external_first_app,
    sekrit_identity,
    sekrit_installer_identity,
    tmp_path,
):
    """A macOS GUI app can be packaged as a .pkg installer."""
    external_first_app.packaging_format = "pkg"

    # Select a codesigning identity
    package_command.select_identity.side_effect = [
        sekrit_identity,
        sekrit_installer_identity,
    ]

    # Mock the notarization process
    package_command.notarize = mock.Mock()

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    # Create a pre-existing app bundle.
    create_file(
        bundle_path / "installer/root/First App.app/original",
        "Original app",
    )

    # Create a pre-existing package bundle.
    create_file(
        bundle_path / "installer/packages/first-app.pkg",
        "Original package",
    )

    # Create a pre-existing LICENSE
    create_file(
        bundle_path / "installer/resources/LICENSE",
        "Original License",
    )

    # Re-package the app
    package_command.package_app(external_first_app)

    # Two signing identities were selected; the second is an installer identity
    assert package_command.select_identity.mock_calls == [
        mock.call(identity=None),
        mock.call(identity=None, app_identity=sekrit_identity),
    ]

    # The app has been signed
    package_command.sign_app.assert_called_once_with(
        app=external_first_app,
        identity=sekrit_identity,
    )

    # App content has been copied into place.
    assert (bundle_path / "installer/root/First App.app/Contents/Info.plist").is_file()

    # When duplicating the app, symlinks have been preserved
    assert (
        bundle_path
        / "installer/root/First App.app/Contents/Frameworks/Extras.framework/Extras"
    ).is_symlink()

    # The license has been updated.
    assert (bundle_path / "installer/resources/LICENSE").read_text(
        encoding="utf-8"
    ) == "The Actual First App License"

    # The component list has been updated.
    with (bundle_path / "installer/components.plist").open("rb") as f:
        components = plistlib.load(f)

        assert components == [
            {
                "BundleHasStrictIdentifier": True,
                "BundleIsRelocatable": False,
                "BundleIsVersionChecked": True,
                "BundleOverwriteAction": "upgrade",
                "RootRelativeBundlePath": "First App.app",
            }
        ]

    assert package_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                "pkgbuild",
                "--root",
                bundle_path / "installer/root",
                "--component-plist",
                bundle_path / "installer/components.plist",
                "--install-location",
                "/Applications",
                bundle_path / "installer/packages/first-app.pkg",
            ],
            check=True,
        ),
        mock.call(
            [
                "productbuild",
                "--distribution",
                bundle_path / "installer/Distribution.xml",
                "--package-path",
                bundle_path / "installer/packages",
                "--resources",
                bundle_path / "installer/resources",
                "--sign",
                "CAFEFACE",
                tmp_path / "base_path/dist/First App-0.0.1.pkg",
            ],
            check=True,
        ),
    ]

    # Notarization was performed with the installer identity
    package_command.notarize.assert_called_once_with(
        external_first_app,
        identity=sekrit_identity,
        installer_identity=sekrit_installer_identity,
    )
