import os
from unittest import mock

import pytest

import briefcase.integrations.xcode
from briefcase.exceptions import BriefcaseCommandError


def test_package_formats(package_command):
    """Packaging formats are as expected."""
    assert package_command.packaging_formats == ["zip", "dmg", "pkg"]
    # The default format is encoded as None, and then updated
    # as part of app verification.
    assert package_command.default_packaging_format is None


@pytest.mark.parametrize(
    "is_console_app, packaging_format, actual_format",
    [
        (False, None, "dmg"),  # default for GUI app is DMG
        (False, "dmg", "dmg"),
        (False, "app", "app"),
        (False, "pkg", "pkg"),
        (True, None, "pkg"),  # default for console app is PKG
        (True, "pkg", "pkg"),
    ],
)
def test_effective_format(
    package_command,
    first_app_with_binaries,
    is_console_app,
    packaging_format,
    actual_format,
):
    """The packaging format varies depending on the app type."""

    first_app_with_binaries.packaging_format = packaging_format
    first_app_with_binaries.console_app = is_console_app
    package_command.verify_app(first_app_with_binaries)

    assert first_app_with_binaries.packaging_format == actual_format


@pytest.mark.parametrize("packaging_format", ["zip", "dmg"])
def test_console_invalid_formats(
    package_command,
    first_app_with_binaries,
    packaging_format,
):
    """Some packaging formats are not valid for console apps."""

    first_app_with_binaries.packaging_format = packaging_format
    first_app_with_binaries.console_app = True
    with pytest.raises(
        BriefcaseCommandError,
        match=r"macOS console apps must be distributed in PKG format\.",
    ):
        package_command.verify_app(first_app_with_binaries)


def test_no_notarize_option(package_command):
    """The --no-notarize option can be parsed."""
    options, overrides = package_command.parse_options(["--no-notarize"])

    assert options == {
        "adhoc_sign": False,
        "identity": None,
        "notarize_app": False,
        "installer_identity": None,
        "sign_installer": True,
        "packaging_format": None,
        "submission_id": None,
        "update": False,
    }
    assert overrides == {}


def test_installer_identity_option(package_command):
    """The --installer_identity option can be parsed."""
    options, overrides = package_command.parse_options(
        ["--installer-identity", "DEADBEEF"]
    )

    assert options == {
        "adhoc_sign": False,
        "identity": None,
        "notarize_app": None,
        "installer_identity": "DEADBEEF",
        "sign_installer": True,
        "packaging_format": None,
        "submission_id": None,
        "update": False,
    }
    assert overrides == {}


def test_no_sign_installer(package_command):
    """The --no-sign-installer option can be parsed."""
    options, overrides = package_command.parse_options(["--no-sign-installer"])

    assert options == {
        "adhoc_sign": False,
        "identity": None,
        "notarize_app": None,
        "installer_identity": None,
        "sign_installer": False,
        "packaging_format": None,
        "submission_id": None,
        "update": False,
    }
    assert overrides == {}


def test_resume(package_command):
    """The --resume option can be parsed."""
    options, overrides = package_command.parse_options(["--resume", "cafe-beef-1234"])

    assert options == {
        "adhoc_sign": False,
        "identity": None,
        "notarize_app": None,
        "installer_identity": None,
        "sign_installer": True,
        "packaging_format": None,
        "submission_id": "cafe-beef-1234",
        "update": False,
    }
    assert overrides == {}


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


def test_package_app(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
    capsys,
):
    """A macOS App is packaged as a signed, notarized DMG by default."""
    # Select a codesigning identity
    package_command.select_identity.return_value = sekrit_identity

    # Package the app. Sign and notarize by default. Use the base command's interface to
    # ensure the full cleanup process is tested.
    package_command._package_app(
        first_app_with_binaries,
        update=False,
        packaging_format="dmg",
    )

    # We verified we aren't on iCloud
    package_command.verify_not_on_icloud.assert_called_once_with(
        first_app_with_binaries
    )

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=sekrit_identity,
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
        identity=sekrit_identity,
    )

    # A request was made to notarize the DMG
    package_command.notarize.assert_called_once_with(
        first_app_with_binaries,
        identity=sekrit_identity,
    )

    # The app doesn't specify an app icon or installer icon, so there's no
    # mention about the DMG installer icon in the console log.
    assert "DMG installer icon" not in capsys.readouterr().out


def test_no_notarization(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
    capsys,
):
    """A macOS App can be packaged as a signed DMG without notarization."""
    # Select a codesigning identity
    package_command.select_identity.return_value = sekrit_identity

    # Package the app; sign by default, but disable notarization. Use the base command's
    # interface to ensure the full cleanup process is tested.
    package_command._package_app(
        first_app_with_binaries,
        notarize_app=False,
        update=False,
        packaging_format="dmg",
    )

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=sekrit_identity,
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
        identity=sekrit_identity,
    )

    # A request was made to notarize the DMG
    package_command.notarize.assert_not_called()

    # The app doesn't specify an app icon or installer icon, so there's no
    # mention about the DMG installer icon in the console log.
    assert "DMG installer icon" not in capsys.readouterr().out


def test_adhoc_sign(
    package_command,
    first_app_with_binaries,
    adhoc_identity,
    tmp_path,
):
    """A macOS App can be packaged and signed with ad-hoc identity."""
    # Package the app with an ad-hoc identity. Explicitly disable notarization (can't
    # ad-hoc notarize an app). Use the base command's interface to ensure the full
    # cleanup process is tested.
    package_command._package_app(
        first_app_with_binaries,
        update=False,
        packaging_format="dmg",
        adhoc_sign=True,
        notarize_app=False,
    )

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=adhoc_identity,
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
        identity=adhoc_identity,
    )

    # No request was made to notarize
    package_command.notarize.assert_not_called()


def test_notarize_adhoc_signed(package_command, first_app_with_binaries):
    """A macOS App cannot be notarized if ad-hoc signing is requested."""

    # Package the app without code signing. Use the base command's interface to ensure
    # the full cleanup process is tested.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Can't notarize an app with an ad-hoc signing identity",
    ):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format="dmg",
            notarize_app=True,
            adhoc_sign=True,
        )

    # No code signing or notarization has been performed.
    assert package_command.select_identity.call_count == 0
    assert package_command.sign_app.call_count == 0
    assert package_command.sign_file.call_count == 0
    assert package_command.notarize.call_count == 0


def test_notarize_adhoc_signed_via_prompt(
    package_command,
    first_app_with_binaries,
    adhoc_identity,
):
    """Notarization is rejected if the user selects the adhoc identity."""

    package_command.select_identity.return_value = adhoc_identity

    # Package the app without code signing. Use the base command's interface to ensure the full
    # cleanup process is tested.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Can't notarize an app with an ad-hoc signing identity",
    ):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format="dmg",
            notarize_app=True,
        )

    # No code signing or notarization has been performed.
    assert package_command.select_identity.call_count == 1
    assert package_command.sign_app.call_count == 0
    assert package_command.sign_file.call_count == 0
    assert package_command.notarize.call_count == 0


def test_adhoc_sign_default_no_notarization(
    package_command,
    first_app_with_binaries,
    adhoc_identity,
    tmp_path,
):
    """An ad-hoc signed app is not notarized by default."""
    # Package the app with an ad-hoc identity; notarization will be disabled as a
    # default. Use the base command's interface to ensure the full cleanup process is
    # tested.
    package_command._package_app(
        first_app_with_binaries,
        update=False,
        packaging_format="dmg",
        adhoc_sign=True,
    )

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=adhoc_identity,
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
        identity=adhoc_identity,
    )

    # No request was made to notarize
    package_command.notarize.assert_not_called()


def test_sign_failure(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
):
    """If the signing process can't be completed, an error is raised."""

    # Select a codesigning identity
    package_command.select_identity.return_value = sekrit_identity

    # Raise an error when attempting to sign the app
    package_command.sign_app.side_effect = BriefcaseCommandError("Unable to code sign")

    # Attempt to package the app; it should raise an error. Use the base command's
    # interface to ensure the full cleanup process is tested.
    with pytest.raises(BriefcaseCommandError, match=r"Unable to code sign"):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format="dmg",
        )

    # A request has been made to sign the app
    package_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=sekrit_identity,
    )

    # dmgbuild has not been called
    package_command.dmgbuild.build_dmg.assert_not_called()

    # No attempt was made to sign the dmg either
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    package_command.sign_file.assert_not_called()
