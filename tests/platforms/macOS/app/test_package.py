import os
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS.app import macOSAppPackageCommand


@pytest.fixture
def package_command(tmp_path):
    command = macOSAppPackageCommand(base_path=tmp_path)

    command.select_identity = mock.MagicMock()
    command.sign_app = mock.MagicMock()
    command.sign_file = mock.MagicMock()
    command.dmgbuild = mock.MagicMock()

    return command


def test_package_app(package_command, first_app_with_binaries, tmp_path, capsys):
    "A macOS App can be packaged"
    # Select a codesigning identity
    package_command.select_identity.return_value = "Sekrit identity (DEADBEEF)"

    # Package the app
    package_command.package_app(first_app_with_binaries)

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries, identity="Sekrit identity (DEADBEEF)"
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "macOS" / "First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(tmp_path / "macOS" / "app" / "First App" / "First App.app")
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
        os.fsdecode(tmp_path / "macOS" / "First App-0.0.1.dmg"),
        identity="Sekrit identity (DEADBEEF)",
    )

    # The app doesn't specify an app icon or installer icon, so there's no
    # mention about the DMG installer icon in the console log.
    assert "DMG installer icon" not in capsys.readouterr().out


def test_package_app_sign_failure(package_command, first_app_with_binaries, tmp_path):
    "If the signing process can't be completed, an error is raised"

    # Select a codesigning identity
    package_command.select_identity.return_value = "Sekrit identity (DEADBEEF)"

    # Raise an error when attempting to sign the app
    package_command.sign_app.side_effect = BriefcaseCommandError("Unable to code sign")

    # Attempt to package the app; it should raise an error
    with pytest.raises(BriefcaseCommandError, match=r"Unable to code sign"):
        package_command.package_app(first_app_with_binaries)

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries, identity="Sekrit identity (DEADBEEF)"
    )

    # dmgbuild has not been called
    package_command.dmgbuild.build_dmg.assert_not_called()

    # No attempt was made to sign the dmg either
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    package_command.sign_file.assert_not_called()


def test_package_app_no_sign(package_command, first_app_with_binaries, tmp_path):
    "A macOS App can be packaged without signing"

    # Package the app without code signing
    package_command.package_app(first_app_with_binaries, sign_app=False)

    # No code signing has been performed.
    assert package_command.select_identity.call_count == 0
    assert package_command.sign_app.call_count == 0
    assert package_command.sign_file.call_count == 0


def test_package_app_adhoc_sign(package_command, first_app_with_binaries, tmp_path):
    "A macOS App can be packaged and signed with adhoc identity"

    # Package the app with an adhoc identity
    package_command.package_app(first_app_with_binaries, adhoc_sign=True)

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries, identity="-"
    )

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "macOS" / "First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(tmp_path / "macOS" / "app" / "First App" / "First App.app")
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
        os.fsdecode(tmp_path / "macOS" / "First App-0.0.1.dmg"), identity="-"
    )


def test_package_app_no_dmg(package_command, first_app_with_binaries, tmp_path):
    "A macOS App can be packaged without building dmg"
    # Select a code signing identity
    package_command.select_identity.return_value = "Sekrit identity (DEADBEEF)"

    # Package the app in app (not DMG) format
    package_command.package_app(first_app_with_binaries, packaging_format="app")

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries, identity="Sekrit identity (DEADBEEF)"
    )

    # No dmg was built.
    assert package_command.dmgbuild.build_dmg.call_count == 0

    # If the DMG doesn't exist, it can't be signed either.
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    assert package_command.sign_file.call_count == 0


def test_dmg_with_installer_icon(package_command, first_app_with_binaries, tmp_path):
    "An installer icon can be specified for a DMG"
    # Specify an installer icon, and create the matching file.
    first_app_with_binaries.installer_icon = "pretty"
    with open(tmp_path / "pretty.icns", "wb") as f:
        f.write(b"A pretty installer icon")

    # Package the app without signing
    package_command.package_app(first_app_with_binaries, sign_app=False)

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "macOS" / "First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(tmp_path / "macOS" / "app" / "First App" / "First App.app")
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
            "icon": os.fsdecode(tmp_path / "pretty.icns"),
        },
    )


def test_dmg_with_missing_installer_icon(
    package_command, first_app_with_binaries, tmp_path, capsys
):
    "If an installer icon is specified, but the specific file is missing, there is a warning"
    # Specify an installer icon, but don't create the matching file.
    first_app_with_binaries.installer_icon = "pretty"

    # Package the app without signing
    package_command.package_app(first_app_with_binaries, sign_app=False)

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "macOS" / "First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(tmp_path / "macOS" / "app" / "First App" / "First App.app")
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
    package_command, first_app_with_binaries, tmp_path
):
    "An installer will fall back to an app icon for a DMG"
    # Specify an app icon, and create the matching file.
    first_app_with_binaries.icon = "pretty_app"
    with open(tmp_path / "pretty_app.icns", "wb") as f:
        f.write(b"A pretty app icon")

    # Package the app without signing
    package_command.package_app(first_app_with_binaries, sign_app=False)

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "macOS" / "First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(tmp_path / "macOS" / "app" / "First App" / "First App.app")
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
            "icon": os.fsdecode(tmp_path / "pretty_app.icns"),
        },
    )


def test_dmg_with_missing_app_installer_icon(
    package_command, first_app_with_binaries, tmp_path, capsys
):
    "If an app icon is specified, but the specific file is missing, there is a warning"
    # Specify an app icon, but don't create the matching file.
    first_app_with_binaries.icon = "pretty_app"

    # Package the app without signing
    package_command.package_app(first_app_with_binaries, sign_app=False)

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "macOS" / "First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(tmp_path / "macOS" / "app" / "First App" / "First App.app")
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
    package_command, first_app_with_binaries, tmp_path
):
    "An installer can be built with an installer background"
    # Specify an installer background, and create the matching file.
    first_app_with_binaries.installer_background = "pretty_background"
    with open(tmp_path / "pretty_background.png", "wb") as f:
        f.write(b"A pretty background")

    # Package the app without signing
    package_command.package_app(first_app_with_binaries, sign_app=False)

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "macOS" / "First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(tmp_path / "macOS" / "app" / "First App" / "First App.app")
            ],
            "symlinks": {"Applications": "/Applications"},
            "icon_locations": {
                "First App.app": (75, 75),
                "Applications": (225, 75),
            },
            "window_rect": ((600, 600), (350, 150)),
            "icon_size": 64,
            "text_size": 12,
            "background": os.fsdecode(tmp_path / "pretty_background.png"),
        },
    )


def test_dmg_with_missing_installer_background(
    package_command, first_app_with_binaries, tmp_path, capsys
):
    "If an installer image is specified, but the specific file is missing, there is a warning"
    # Specify an installer background, but don't create the matching file.
    first_app_with_binaries.installer_background = "pretty_background"

    # Package the app without signing
    package_command.package_app(first_app_with_binaries, sign_app=False)

    # The DMG has been built as expected
    package_command.dmgbuild.build_dmg.assert_called_once_with(
        filename=os.fsdecode(tmp_path / "macOS" / "First App-0.0.1.dmg"),
        volume_name="First App 0.0.1",
        settings={
            "files": [
                os.fsdecode(tmp_path / "macOS" / "app" / "First App" / "First App.app")
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
