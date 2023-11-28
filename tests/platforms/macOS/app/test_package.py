import os
import subprocess
from unittest import mock
from zipfile import ZipFile

import pytest

import briefcase.integrations.xcode
from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS.app import macOSAppPackageCommand


@pytest.fixture
def package_command(tmp_path):
    command = macOSAppPackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    command.select_identity = mock.MagicMock()
    command.sign_app = mock.MagicMock()
    command.sign_file = mock.MagicMock()
    command.notarize = mock.MagicMock()
    command.dmgbuild = mock.MagicMock()
    command.tools.subprocess = mock.MagicMock(spec=subprocess)

    return command


def test_package_formats(package_command):
    """Packaging formats are as expected."""
    assert package_command.packaging_formats == ["app", "dmg"]
    assert package_command.default_packaging_format == "dmg"


def test_device_option(package_command):
    """The -d option can be parsed."""
    options, overrides = package_command.parse_options(["--no-notarize"])

    assert options == {
        "adhoc_sign": False,
        "identity": None,
        "notarize_app": False,
        "packaging_format": "dmg",
        "update": False,
    }
    assert overrides == {}


def test_package_app(package_command, first_app_with_binaries, tmp_path, capsys):
    """A macOS App can be packaged."""
    # Select a codesigning identity
    package_command.select_identity.return_value = (
        "CAFEBEEF",
        "Sekrit identity (DEADBEEF)",
    )

    # Package the app. Sign and notarize by default
    package_command.package_app(first_app_with_binaries)

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries, identity="CAFEBEEF"
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "base_path/dist/First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "macos"
                    / "app"
                    / "First App.app"
                )
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
        },
    )

    # A request was made to sign the DMG as well.
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    package_command.sign_file.assert_called_once_with(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        identity="CAFEBEEF",
    )

    # A request was made to notarize the DMG
    package_command.notarize.assert_called_once_with(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        team_id="DEADBEEF",
    )

    # The app doesn't specify an app icon or installer icon, so there's no
    # mention about the DMG installer icon in the console log.
    assert "DMG installer icon" not in capsys.readouterr().out


def test_package_app_no_notarization(
    package_command,
    first_app_with_binaries,
    tmp_path,
    capsys,
):
    """A macOS App can be packaged without notarization."""
    # Select a codesigning identity
    package_command.select_identity.return_value = (
        "CAFEBEEF",
        "Sekrit identity (DEADBEEF)",
    )

    # Package the app; sign by default, but disable notarization
    package_command.package_app(first_app_with_binaries, notarize_app=False)

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries, identity="CAFEBEEF"
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "base_path/dist/First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "macos"
                    / "app"
                    / "First App.app"
                )
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
        },
    )

    # A request was made to sign the DMG as well.
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    package_command.sign_file.assert_called_once_with(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        identity="CAFEBEEF",
    )

    # A request was made to notarize the DMG
    package_command.notarize.assert_not_called()

    # The app doesn't specify an app icon or installer icon, so there's no
    # mention about the DMG installer icon in the console log.
    assert "DMG installer icon" not in capsys.readouterr().out


def test_package_app_sign_failure(package_command, first_app_with_binaries, tmp_path):
    """If the signing process can't be completed, an error is raised."""

    # Select a codesigning identity
    package_command.select_identity.return_value = (
        "CAFEBEEF",
        "Sekrit identity (DEADBEEF)",
    )

    # Raise an error when attempting to sign the app
    package_command.sign_app.side_effect = BriefcaseCommandError("Unable to code sign")

    # Attempt to package the app; it should raise an error
    with pytest.raises(BriefcaseCommandError, match=r"Unable to code sign"):
        package_command.package_app(first_app_with_binaries)

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity="CAFEBEEF",
    )

    # dmgbuild has not been called
    package_command.dmgbuild.build_dmg.assert_not_called()

    # No attempt was made to sign the dmg either
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    package_command.sign_file.assert_not_called()


def test_package_app_notarize_adhoc_signed(package_command, first_app_with_binaries):
    """A macOS App cannot be notarized if ad-hoc signing is requested."""

    # Package the app without code signing
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Can't notarize an app with an ad-hoc signing identity",
    ):
        package_command.package_app(
            first_app_with_binaries,
            notarize_app=True,
            adhoc_sign=True,
        )

    # No code signing or notarization has been performed.
    assert package_command.select_identity.call_count == 0
    assert package_command.sign_app.call_count == 0
    assert package_command.sign_file.call_count == 0
    assert package_command.notarize.call_count == 0


def test_package_app_notarize_adhoc_signed_via_prompt(
    package_command, first_app_with_binaries
):
    """A macOS App cannot be notarized if ad-hoc signing is requested."""

    package_command.select_identity.return_value = (
        "-",
        (
            "Ad-hoc identity. The resulting package will run but cannot be "
            "re-distributed."
        ),
    )
    # Package the app without code signing
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Can't notarize an app with an ad-hoc signing identity",
    ):
        package_command.package_app(
            first_app_with_binaries,
            notarize_app=True,
        )

    # No code signing or notarization has been performed.
    assert package_command.select_identity.call_count == 1
    assert package_command.sign_app.call_count == 0
    assert package_command.sign_file.call_count == 0
    assert package_command.notarize.call_count == 0


def test_package_app_adhoc_signed_via_prompt(
    package_command, first_app_with_binaries, tmp_path
):
    """A macOS App cannot be notarized if ad-hoc signing is requested."""

    package_command.select_identity.return_value = (
        "-",
        (
            "Ad-hoc identity. The resulting package will run but cannot be "
            "re-distributed."
        ),
    )
    package_command.package_app(
        first_app_with_binaries,
        notarize_app=False,
    )

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity="-",
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "base_path/dist/First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "macos"
                    / "app"
                    / "First App.app"
                )
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
        },
    )

    # A request was made to sign the DMG as well.
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    package_command.sign_file.assert_called_once_with(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        identity="-",
    )

    # No request was made to notarize
    package_command.notarize.assert_not_called()


def test_package_app_adhoc_sign(package_command, first_app_with_binaries, tmp_path):
    """A macOS App can be packaged and signed with ad-hoc identity."""

    # Package the app with an ad-hoc identity.
    # Explicitly disable notarization (can't ad-hoc notarize an app)
    package_command.package_app(
        first_app_with_binaries,
        adhoc_sign=True,
        notarize_app=False,
    )

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity="-",
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "base_path/dist/First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "macos"
                    / "app"
                    / "First App.app"
                )
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
        },
    )

    # A request was made to sign the DMG as well.
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    package_command.sign_file.assert_called_once_with(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        identity="-",
    )

    # No request was made to notarize
    package_command.notarize.assert_not_called()


def test_package_app_adhoc_sign_default_notarization(
    package_command, first_app_with_binaries, tmp_path
):
    """An ad-hoc signed app is not notarized by default."""

    # Package the app with an ad-hoc identity; notarization will
    # be disabled as a default
    package_command.package_app(
        first_app_with_binaries,
        adhoc_sign=True,
    )

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity="-",
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "base_path/dist/First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "macos"
                    / "app"
                    / "First App.app"
                )
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
        },
    )

    # A request was made to sign the DMG as well.
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    package_command.sign_file.assert_called_once_with(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        identity="-",
    )

    # No request was made to notarize
    package_command.notarize.assert_not_called()


def test_package_bare_app(package_command, first_app_with_binaries, tmp_path):
    """A macOS App can be packaged without building dmg."""
    # Select app packaging
    first_app_with_binaries.packaging_format = "app"

    # Select a code signing identity
    package_command.select_identity.return_value = (
        "CAFEBEEF",
        "Sekrit identity (DEADBEEF)",
    )

    # Package the app in app (not DMG) format
    first_app_with_binaries.packaging_format = "app"
    package_command.package_app(first_app_with_binaries)

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries, identity="CAFEBEEF"
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
        team_id="DEADBEEF",
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
            "First App.app/Contents/Resources/",
            "First App.app/Contents/Resources/app_packages/",
            "First App.app/Contents/Resources/app_packages/Extras.app/",
            "First App.app/Contents/Resources/app_packages/Extras.app/Contents/",
            "First App.app/Contents/Resources/app_packages/Extras.app/Contents/MacOS/",
            "First App.app/Contents/Resources/app_packages/Extras.app/Contents/MacOS/Extras",
            "First App.app/Contents/Resources/app_packages/first.other",
            "First App.app/Contents/Resources/app_packages/first_dylib.dylib",
            "First App.app/Contents/Resources/app_packages/first_so.so",
            "First App.app/Contents/Resources/app_packages/other_binary",
            "First App.app/Contents/Resources/app_packages/second.other",
            "First App.app/Contents/Resources/app_packages/special.binary",
            "First App.app/Contents/Resources/app_packages/subfolder/",
            "First App.app/Contents/Resources/app_packages/subfolder/second_dylib.dylib",
            "First App.app/Contents/Resources/app_packages/subfolder/second_so.so",
            "First App.app/Contents/Resources/app_packages/unknown.binary",
        ]


def test_package_bare_app_no_notarization(package_command, first_app_with_binaries):
    """A macOS App can be packaged without building dmg, and without notarization."""
    # Select app packaging
    first_app_with_binaries.packaging_format = "app"

    # Select a code signing identity
    package_command.select_identity.return_value = (
        "CAFEBEEF",
        "Sekrit identity (DEADBEEF)",
    )

    # Package the app in app (not DMG) format, disabling notarization
    first_app_with_binaries.packaging_format = "app"
    package_command.package_app(
        first_app_with_binaries,
        notarize_app=False,
    )

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity="CAFEBEEF",
    )

    # No request has been made to notarize the app
    package_command.notarize.assert_not_called()

    # No dmg was built.
    assert package_command.dmgbuild.build_dmg.call_count == 0

    # If the DMG doesn't exist, it can't be signed either.
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    assert package_command.sign_file.call_count == 0


def test_dmg_with_installer_icon(package_command, first_app_with_binaries, tmp_path):
    """An installer icon can be specified for a DMG."""
    # Specify an installer icon, and create the matching file.
    first_app_with_binaries.installer_icon = "pretty"
    with open(tmp_path / "base_path/pretty.icns", "wb") as f:
        f.write(b"A pretty installer icon")

    # Package the app without signing or notarization
    package_command.package_app(
        first_app_with_binaries,
        notarize_app=False,
        adhoc_sign=True,
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "base_path/dist/First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "macos"
                    / "app"
                    / "First App.app"
                )
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
            "icon": os.fsdecode(tmp_path / "base_path/pretty.icns"),
        },
    )


def test_dmg_with_missing_installer_icon(
    package_command,
    first_app_with_binaries,
    tmp_path,
    capsys,
):
    """If an installer icon is specified, but the specific file is missing, there is a
    warning."""
    # Specify an installer icon, but don't create the matching file.
    first_app_with_binaries.installer_icon = "pretty"
    first_app_with_binaries.packaging_format = "dmg"

    # Package the app without signing or notarization
    package_command.package_app(
        first_app_with_binaries,
        notarize_app=False,
        adhoc_sign=True,
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "base_path/dist/First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "macos"
                    / "app"
                    / "First App.app"
                )
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
        },
    )

    # The warning about a missing icon was output
    assert (
        "Can't find pretty.icns to use as DMG installer icon\n"
        in capsys.readouterr().out
    )


def test_dmg_with_app_installer_icon(
    package_command,
    first_app_with_binaries,
    tmp_path,
):
    """An installer will fall back to an app icon for a DMG."""
    # Specify an app icon, and create the matching file.
    first_app_with_binaries.icon = "pretty_app"
    with open(tmp_path / "base_path/pretty_app.icns", "wb") as f:
        f.write(b"A pretty app icon")

    # Package the app without signing or notarization
    package_command.package_app(
        first_app_with_binaries,
        notarize_app=False,
        adhoc_sign=True,
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "base_path/dist/First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "macos"
                    / "app"
                    / "First App.app"
                )
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
            "icon": os.fsdecode(tmp_path / "base_path/pretty_app.icns"),
        },
    )


def test_dmg_with_missing_app_installer_icon(
    package_command,
    first_app_with_binaries,
    tmp_path,
    capsys,
):
    """If an app icon is specified, but the specific file is missing, there is a
    warning."""
    # Specify an app icon, but don't create the matching file.
    first_app_with_binaries.icon = "pretty_app"

    # Package the app without signing or notarization
    package_command.package_app(
        first_app_with_binaries,
        notarize_app=False,
        adhoc_sign=True,
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "base_path/dist/First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "macos"
                    / "app"
                    / "First App.app"
                )
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
        },
    )

    # The warning about a missing icon was output
    assert (
        "Can't find pretty_app.icns to use as fallback DMG installer icon\n"
        in capsys.readouterr().out
    )


def test_dmg_with_installer_background(
    package_command,
    first_app_with_binaries,
    tmp_path,
):
    """An installer can be built with an installer background."""
    # Specify an installer background, and create the matching file.
    first_app_with_binaries.installer_background = "pretty_background"
    with open(tmp_path / "base_path/pretty_background.png", "wb") as f:
        f.write(b"A pretty background")

    # Package the app without signing or notarization
    package_command.package_app(
        first_app_with_binaries,
        notarize_app=False,
        adhoc_sign=True,
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "base_path/dist/First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "macos"
                    / "app"
                    / "First App.app"
                )
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
            "background": os.fsdecode(tmp_path / "base_path/pretty_background.png"),
        },
    )


def test_dmg_with_missing_installer_background(
    package_command,
    first_app_with_binaries,
    tmp_path,
    capsys,
):
    """If an installer image is specified, but the specific file is missing, there is a
    warning."""
    # Specify an installer background, but don't create the matching file.
    first_app_with_binaries.installer_background = "pretty_background"
    first_app_with_binaries.packaging_format = "dmg"

    # Package the app without signing or notarization
    package_command.package_app(
        first_app_with_binaries,
        notarize_app=False,
        adhoc_sign=True,
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "base_path/dist/First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(
                    tmp_path
                    / "base_path"
                    / "build"
                    / "first-app"
                    / "macos"
                    / "app"
                    / "First App.app"
                )
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
        },
    )

    # The warning about a missing background was output
    assert (
        "Can't find pretty_background.png to use as DMG background\n"
        in capsys.readouterr().out
    )


def test_verify(package_command, monkeypatch):
    """If you're on macOS, you can verify tools."""
    package_command.tools.host_os = "Darwin"

    # Mock the existence of the command line tools
    mock_ensure_command_line_tools_are_installed = mock.MagicMock()
    monkeypatch.setattr(
        briefcase.integrations.xcode.XcodeCliTools,
        "ensure_command_line_tools_are_installed",
        mock_ensure_command_line_tools_are_installed,
    )
    mock_confirm_xcode_license_accepted = mock.MagicMock()
    monkeypatch.setattr(
        briefcase.integrations.xcode.XcodeCliTools,
        "confirm_xcode_license_accepted",
        mock_confirm_xcode_license_accepted,
    )

    package_command.verify_tools()

    assert package_command.tools.xcode_cli is not None
    mock_ensure_command_line_tools_are_installed.assert_called_once_with(
        tools=package_command.tools
    )
    mock_confirm_xcode_license_accepted.assert_called_once_with(
        tools=package_command.tools
    )
