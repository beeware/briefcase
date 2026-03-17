from __future__ import annotations

import os
import plistlib
from pathlib import Path

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.formats.base import BasePackagingFormat, macOSPackageCommandAPI


class macOSDMGPackagingFormat(BasePackagingFormat):
    command: macOSPackageCommandAPI

    @property
    def name(self) -> str:
        return "dmg"

    def distribution_path(self, app: AppConfig) -> Path:
        return self.command.dist_path / f"{app.formal_name}-{app.version}.dmg"

    def package_app(
        self,
        app: AppConfig,
        notarize_app: bool = True,
        identity=None,
        **options,
    ):
        """Package an app as a DMG installer."""
        # Normal packaging pass.
        if identity is None:
            identity = self.command.select_identity(identity=identity)

        if identity.is_adhoc and notarize_app:
            raise BriefcaseCommandError(
                "Can't notarize an app with an ad-hoc signing identity"
            )

        self.command.console.info("Signing app...", prefix=app.app_name)
        self.command.sign_app(app=app, identity=identity)

        dist_path = self.distribution_path(app)
        self.command.console.info("Building DMG...", prefix=app.app_name)

        with self.command.console.wait_bar(f"Building {dist_path.name}..."):
            dmg_settings = {
                "files": [os.fsdecode(self.command.package_path(app))],
                "symlinks": {"Applications": "/Applications"},
                "icon_locations": {
                    self.command.package_path(app).name: (75, 75),
                    "Applications": (225, 75),
                },
                "window_rect": ((600, 600), (350, 150)),
                "icon_size": 64,
                "text_size": 12,
            }

            try:
                icon_filename = self.command.base_path / f"{app.installer_icon}.icns"
                if not icon_filename.exists():
                    self.command.console.warning(
                        f"Can't find {app.installer_icon}.icns "
                        "to use as DMG installer icon"
                    )
                    raise AttributeError()
            except AttributeError:
                # No installer icon specified. Fall back to the app icon
                if app.icon:
                    icon_filename = self.command.base_path / f"{app.icon}.icns"
                    if not icon_filename.exists():
                        self.command.console.warning(
                            f"Can't find {app.icon}.icns "
                            "to use as fallback DMG installer icon"
                        )
                        icon_filename = None
                else:
                    # No app icon specified either
                    icon_filename = None

            if icon_filename:
                dmg_settings["icon"] = os.fsdecode(icon_filename)

            try:
                image_filename = (
                    self.command.base_path / f"{app.installer_background}.png"
                )
                if image_filename.exists():
                    dmg_settings["background"] = os.fsdecode(image_filename)
                else:
                    self.command.console.warning(
                        f"Can't find {app.installer_background}.png "
                        "to use as DMG background"
                    )
            except AttributeError:
                # No installer background image provided
                pass

            self.command.dmgbuild.build_dmg(
                filename=os.fsdecode(dist_path),
                volume_name=f"{app.formal_name} {app.version}",
                settings=dmg_settings,
            )

        self.command.sign_file(dist_path, identity=identity)

        if notarize_app:
            self.command.console.info(
                f"Notarizing DMG with team ID {identity.team_id}...",
                prefix=app.app_name,
            )
            self.command.notarize(app, identity=identity)

    def priority(self, app: AppConfig) -> int:
        # DMG is the default for GUI apps on macOS
        return 10 if not app.console_app else 0


class macOSPKGPackagingFormat(BasePackagingFormat):
    command: macOSPackageCommandAPI

    @property
    def name(self) -> str:
        return "pkg"

    def distribution_path(self, app: AppConfig) -> Path:
        return self.command.dist_path / f"{app.formal_name}-{app.version}.pkg"

    def package_app(
        self,
        app: AppConfig,
        notarize_app: bool = True,
        identity=None,
        sign_installer: bool = True,
        installer_identity=None,
        **options,
    ):
        """Package the app as an installer."""
        if identity is None:
            identity = self.command.select_identity(identity=identity)

        self.command.console.info("Signing app...", prefix=app.app_name)
        self.command.sign_app(app=app, identity=identity)

        # If the user has indicated they want to sign the installer (the default),
        # and the signing identity for the app *isn't* the adhoc identity, select an
        # identity for signing the installer.
        if sign_installer and not identity.is_adhoc:
            installer_identity = self.command.select_identity(
                identity=installer_identity,
                app_identity=identity,
            )
        else:
            installer_identity = None

        dist_path = self.distribution_path(app)
        self.command.console.info("Building PKG...", prefix=app.app_name)

        installer_path = self.command.bundle_path(app) / "installer"

        with self.command.console.wait_bar("Installing license..."):
            license_file = self.command.base_path / "LICENSE"
            if license_file.is_file():
                (installer_path / "resources").mkdir(exist_ok=True)
                self.command.tools.shutil.copy(
                    license_file,
                    installer_path / "resources/LICENSE",
                )
            else:
                raise BriefcaseCommandError("""\
Your project does not contain a LICENSE file.

Create a file named `LICENSE` in the same directory as your `pyproject.toml`
with your app's licensing terms.
""")

        with self.command.console.wait_bar("Copying app into products folder..."):
            installed_app_path = (
                installer_path / "root" / self.command.package_path(app).name
            )
            if installed_app_path.exists():
                self.command.tools.shutil.rmtree(installed_app_path)
            self.command.tools.shutil.copytree(
                self.command.package_path(app),
                installed_app_path,
                symlinks=True,
            )

        components_plist_path = (
            self.command.bundle_path(app) / "installer/components.plist"
        )
        with (
            self.command.console.wait_bar("Writing component manifest..."),
            components_plist_path.open("wb") as components_plist,
        ):
            plistlib.dump(
                [
                    {
                        "BundleHasStrictIdentifier": True,
                        "BundleIsRelocatable": False,
                        "BundleIsVersionChecked": True,
                        "BundleOverwriteAction": "upgrade",
                        "RootRelativeBundlePath": self.command.package_path(app).name,
                    }
                ],
                components_plist,
            )

        if app.console_app:
            install_args = [
                "--install-location",
                f"/Library/{app.formal_name}",
                "--scripts",
                installer_path / "scripts",
            ]
        else:
            install_args = ["--install-location", "/Applications"]

        with self.command.console.wait_bar("Building app package..."):
            installer_packages_path = installer_path / "packages"
            if installer_packages_path.exists():
                self.command.tools.shutil.rmtree(installer_packages_path)
            installer_packages_path.mkdir()

            self.command.tools.subprocess.run(
                [
                    "pkgbuild",
                    "--root",
                    installer_path / "root",
                    "--component-plist",
                    components_plist_path,
                    *install_args,
                    installer_packages_path / f"{app.app_name}.pkg",
                ],
                check=True,
            )

        with self.command.console.wait_bar(f"Building {dist_path.name}..."):
            if installer_identity:
                signing_options = ["--sign", installer_identity.id]
            else:
                signing_options = []

            self.command.tools.subprocess.run(
                [
                    "productbuild",
                    "--distribution",
                    installer_path / "Distribution.xml",
                    "--package-path",
                    installer_path / "packages",
                    "--resources",
                    installer_path / "resources",
                    *signing_options,
                    dist_path,
                ],
                check=True,
            )

        if notarize_app:
            self.command.console.info(
                f"Notarizing PKG with team ID {installer_identity.team_id if installer_identity else identity.team_id}...",  # noqa: E501
                prefix=app.app_name,
            )
            self.command.notarize(
                app,
                identity=identity,
                installer_identity=installer_identity,
            )

    def priority(self, app: AppConfig) -> int:
        # PKG is the default for console apps on macOS
        return 10 if app.console_app else 0


class macOSZipPackagingFormat(BasePackagingFormat):
    command: macOSPackageCommandAPI

    @property
    def name(self) -> str:
        return "zip"

    def distribution_path(self, app: AppConfig) -> Path:
        return self.command.dist_path / f"{app.formal_name}-{app.version}.app.zip"

    def package_app(self, app: AppConfig, **options):
        self.command.console.info("Building zip file...", prefix=app.app_name)
        with self.command.console.wait_bar("Packing..."):
            self.command.archive_app(app, self.distribution_path(app))

    def priority(self, app: AppConfig) -> int:
        # Zip is a supported format, but never the default
        return 1
