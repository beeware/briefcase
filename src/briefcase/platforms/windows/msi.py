import os
import struct
import subprocess
import sys
import uuid

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import BaseConfig, parsed_version
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.wix import WiX
from briefcase.platforms.windows import WindowsMixin


class WindowsMSIMixin(WindowsMixin):
    output_format = "msi"

    def binary_path(self, app):
        return self.bundle_path(app)

    def distribution_path(self, app, packaging_format):
        return self.platform_path / f"{app.formal_name}-{app.version}.msi"

    def verify_tools(self):
        super().verify_tools()
        self.wix = WiX.verify(self)


class WindowsMSICreateCommand(WindowsMSIMixin, CreateCommand):
    description = "Create and populate a Windows app."

    @property
    def support_package_url_query(self):
        """The query arguments to use in a support package query request."""
        return [
            ("platform", self.platform),
            ("version", self.python_version_tag),
            ("arch", "amd64" if (struct.calcsize("P") * 8) == 64 else "win32"),
        ]

    def output_format_template_context(self, app: BaseConfig):
        """Additional template context required by the output format.

        :param app: The config object for the app
        """
        # WiX requires a 3-element, integer-only version number. If a version
        # triple isn't explicitly provided, generate one by stripping any
        # non-numeric portions from the version number.
        # If there are less than 3 numeric parts, 0s will be appended.
        try:
            version_triple = app.version_triple
        except AttributeError:
            parsed = parsed_version(app.version)
            version_triple = ".".join(
                ([str(v) for v in parsed.release] + ["0", "0"])[:3]
            )

        # The application needs a unique GUID.
        # This is used to track the application, even if the application
        # name changes. We can generate a default GUID using the bundle
        # and the formal name; but you'll need to manually set this value
        # if you ever change those two keys.
        try:
            guid = app.guid
        except AttributeError:
            # Create a DNS domain by reversing the bundle identifier
            domain = ".".join([app.app_name] + app.bundle.split(".")[::-1])
            guid = uuid.uuid5(uuid.NAMESPACE_DNS, domain)
            self.logger.info(f"Assigning {app.app_name} an application GUID of {guid}")

        try:
            install_scope = "perMachine" if app.system_installer else "perUser"
        except AttributeError:
            # system_installer not defined in config; default to perUser install.
            install_scope = "perUser"

        return {
            "version_triple": version_triple,
            "guid": str(guid),
            "install_scope": install_scope,
        }

    def install_app_support_package(self, app: BaseConfig):
        """Install, then modify the default support package."""
        # Install the support package using the normal install logic.
        super().install_app_support_package(app)

        # We need to add a ._pth file to include app and app_packages as
        # part of the standard PYTHONPATH. Write a _pth file directly into
        # the support folder, overwriting the default one.
        version_tag = f"{sys.version_info.major}{sys.version_info.minor}"
        pth_file = self.support_path(app) / f"python{version_tag}._pth"
        with pth_file.open("w") as f:
            f.write(f"python{version_tag}.zip\n")
            f.write(".\n")
            f.write("..\\\\app\n")
            f.write("..\\\\app_packages\n")


class WindowsMSIUpdateCommand(WindowsMSIMixin, UpdateCommand):
    description = "Update an existing Windows app."


class WindowsMSIBuildCommand(WindowsMSIMixin, BuildCommand):
    description = "Build a Windows app."


class WindowsMSIRunCommand(WindowsMSIMixin, RunCommand):
    description = "Run a Windows app."

    def run_app(self, app: BaseConfig, **kwargs):
        """Start the application.

        :param app: The config object for the app
        """
        self.logger.info("Starting app...", prefix=app.app_name)
        try:
            self.subprocess.run(
                [
                    os.fsdecode(
                        self.binary_path(app) / "src" / "python" / "pythonw.exe"
                    ),
                    "-m",
                    app.module_name,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to start app {app.app_name}.") from e


class WindowsMSIPackageCommand(WindowsMSIMixin, PackageCommand):
    description = "Package an MSI for a Windows app."

    def package_app(self, app: BaseConfig, **kwargs):
        """Build an application.

        :param app: The application to build
        """
        self.logger.info("Building MSI...", prefix=app.app_name)

        try:
            self.logger.info("Compiling application manifest...")
            with self.input.wait_bar("Compiling..."):
                self.subprocess.run(
                    [
                        self.wix.heat_exe,
                        "dir",
                        "src",
                        "-nologo",  # Don't display startup text
                        "-gg",  # Generate GUIDs
                        "-sfrag",  # Suppress fragment generation for directories
                        "-sreg",  # Suppress registry harvesting
                        "-srd",  # Suppress harvesting the root directory
                        "-scom",  # Suppress harvesting COM components
                        "-dr",
                        f"{app.module_name}_ROOTDIR",  # Root directory reference name
                        "-cg",
                        f"{app.module_name}_COMPONENTS",  # Root component group name
                        "-var",
                        "var.SourceDir",  # variable to use as the source dir
                        "-out",
                        f"{app.app_name}-manifest.wxs",
                    ],
                    check=True,
                    cwd=self.bundle_path(app),
                )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to generate manifest for app {app.app_name}."
            ) from e

        try:
            self.logger.info("Compiling application installer...")
            with self.input.wait_bar("Compiling..."):
                self.subprocess.run(
                    [
                        self.wix.candle_exe,
                        "-nologo",  # Don't display startup text
                        "-ext",
                        "WixUtilExtension",
                        "-ext",
                        "WixUIExtension",
                        "-dSourceDir=src",
                        f"{app.app_name}.wxs",
                        f"{app.app_name}-manifest.wxs",
                    ],
                    check=True,
                    cwd=self.bundle_path(app),
                )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to compile app {app.app_name}.") from e

        try:
            self.logger.info("Linking application installer...")
            with self.input.wait_bar("Linking..."):
                self.subprocess.run(
                    [
                        self.wix.light_exe,
                        "-nologo",  # Don't display startup text
                        "-ext",
                        "WixUtilExtension",
                        "-ext",
                        "WixUIExtension",
                        "-loc",
                        "unicode.wxl",
                        "-o",
                        self.distribution_path(app, packaging_format="msi"),
                        f"{app.app_name}.wixobj",
                        f"{app.app_name}-manifest.wixobj",
                    ],
                    check=True,
                    cwd=self.bundle_path(app),
                )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to link app {app.app_name}.") from e


class WindowsMSIPublishCommand(WindowsMSIMixin, PublishCommand):
    description = "Publish a Windows MSI."


# Declare the briefcase command bindings
create = WindowsMSICreateCommand  # noqa
update = WindowsMSIUpdateCommand  # noqa
build = WindowsMSIBuildCommand  # noqa
run = WindowsMSIRunCommand  # noqa
package = WindowsMSIPackageCommand  # noqa
publish = WindowsMSIPublishCommand  # noqa
