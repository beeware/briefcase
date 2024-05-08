import os


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
