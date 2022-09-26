import os
import subprocess
import uuid

from briefcase.commands import CreateCommand, PackageCommand, RunCommand
from briefcase.config import BaseConfig, parsed_version
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.wix import WiX

DEFAULT_OUTPUT_FORMAT = "app"


class WindowsMixin:
    platform = "windows"

    def binary_path(self, app):
        return self.bundle_path(app) / self.packaging_root / f"{app.formal_name}.exe"

    def distribution_path(self, app, packaging_format):
        return self.platform_path / f"{app.formal_name}-{app.version}.msi"


class WindowsCreateCommand(CreateCommand):
    def support_package_filename(self, support_revision):
        return f"python-{self.python_version_tag}.{support_revision}-embed-amd64.zip"

    def support_package_url(self, support_revision):
        return (
            f"https://www.python.org/ftp/python/{self.python_version_tag}.{support_revision}/"
            + self.support_package_filename(support_revision)
        )

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
            # system_installer not defined in config; default to asking the user
            install_scope = None

        return {
            "version_triple": version_triple,
            "guid": str(guid),
            "install_scope": install_scope,
        }


class WindowsRunCommand(RunCommand):
    def run_app(self, app: BaseConfig, **kwargs):
        """Start the application.

        :param app: The config object for the app
        """
        self.logger.info("Starting app...", prefix=app.app_name)
        try:
            # Start streaming logs for the app.
            self.logger.info("=" * 75)
            self.tools.subprocess.run(
                [os.fsdecode(self.binary_path(app))],
                cwd=self.tools.home_path,
                check=True,
                stream_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to start app {app.app_name}.") from e


class WindowsPackageCommand(PackageCommand):
    @property
    def packaging_formats(self):
        return ["msi"]

    @property
    def default_packaging_format(self):
        return "msi"

    def verify_tools(self):
        super().verify_tools()
        WiX.verify(self.tools)

    def package_app(self, app: BaseConfig, **kwargs):
        """Package an application.

        :param app: The application to package
        """
        self.logger.info("Building MSI...", prefix=app.app_name)

        try:
            self.logger.info("Compiling application manifest...")
            with self.input.wait_bar("Compiling..."):
                self.tools.subprocess.run(
                    [
                        self.tools.wix.heat_exe,
                        "dir",
                        os.fsdecode(self.packaging_root),
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
                self.tools.subprocess.run(
                    [
                        self.tools.wix.candle_exe,
                        "-nologo",  # Don't display startup text
                        "-ext",
                        "WixUtilExtension",
                        "-ext",
                        "WixUIExtension",
                        "-arch",
                        "x64",
                        f"-dSourceDir={self.packaging_root}",
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
                self.tools.subprocess.run(
                    [
                        self.tools.wix.light_exe,
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
