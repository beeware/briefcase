import os
import re
import subprocess
import uuid
from typing import List
from pathlib import Path

from briefcase.commands import CreateCommand, PackageCommand, RunCommand
from briefcase.config import AppConfig, parsed_version
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.windows_sdk import WindowsSDK
from briefcase.integrations.wix import WiX

DEFAULT_OUTPUT_FORMAT = "app"


class WindowsMixin:
    platform = "windows"
    supported_host_os = {"Windows"}
    supported_host_os_reason = "Windows applications can only be built on Windows."

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

    def output_format_template_context(self, app: AppConfig):
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
    def run_app(
        self,
        app: BaseConfig,
        test_mode: bool,
        passthrough: List[str],
        **kwargs,
    ):
        """Start the application.

        :param app: The config object for the app
        :param test_mode: Boolean; Is the app running in test mode?
        :param passthrough: The list of arguments to pass to the app
        """
        # Set up the log stream
        kwargs = self._prepare_app_env(app=app, test_mode=test_mode)

        # Start the app in a way that lets us stream the logs
        app_popen = self.tools.subprocess.Popen(
            [os.fsdecode(self.binary_path(app))] + passthrough,
            cwd=self.tools.home_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            **kwargs,
        )

        # Start streaming logs for the app.
        self._stream_app_logs(
            app,
            popen=app_popen,
            test_mode=test_mode,
            clean_output=False,
        )


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
        WindowsSDK.verify(self.tools)

    def get_signing_options(self, identity):
        """Gather configuration for App codesigning.

        :param identity: SHA-1 certificate thumbprint
        :return: dictionary of codesigning options
        """
        options = {}

        if not re.match(r"^[0-9a-f]{40}$", identity, flags=re.IGNORECASE):
            raise BriefcaseCommandError(
                f"Codesigning identify {identity!r} should be a certificate SHA-1 thumbprint."
            )
        options["cert_thumbprint"] = identity

        options["file_digest"] = self.tools.input.text_input(
            "Hashing algorithm for the signatures [sha256]: ",
            default="sha256",
        )

        store = self.tools.input.text_input(
            "Certificate is stored in the Current User's or Local Machine's certificate stores: [Current User]: ",
            default="Current User",
        )
        options["cert_store_location"] = (
            "Local Machine" if store[0].upper() == "L" else "Current User"
        )

        options["cert_store"] = self.tools.input.text_input(
            "Name of the certificate store containing the certificate [My]: ",
            default="My",
        )

        options["timestamp_url"] = self.tools.input.text_input(
            "Timestamp authority server for the signatures [http://timestamp.digicert.com]: ",
            default="http://timestamp.digicert.com",
        )
        options["timestamp_digest"] = self.tools.input.text_input(
            "Hashing algorithm to request for the timestamp server signature [sha256]: ",
            default="sha256",
        )

        return options

    def sign_file(self, app: AppConfig, filepath: Path, options: dict):
        """Sign a file.

        :param app: Application being signed
        :param filepath: Filepath for file to sign
        :param options: Options for signtool signing
        """
        sign_command = [
            self.tools.windows_sdk.signtool_exe,
            "sign",
            "/s",
            options["cert_store"],
            "/sha1",
            options["cert_thumbprint"],
            "/fd",
            options["file_digest"],
            "/d",
            app.description,
            "/du",
            app.url,
            "/tr",
            options["timestamp_url"],
            "/td",
            options["timestamp_digest"],
            # TODO:PR: remove debug
            "/debug",
        ]

        if options["cert_store_location"] == "Local Machine":
            sign_command.append("/sm")

        # Filepath to sign must come last
        sign_command.append(os.fsdecode(filepath))

        try:
            self.tools.subprocess.run(sign_command, check=True)
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to sign {filepath}") from e

    def package_app(self, app: AppConfig, sign_app, identity, **kwargs):
        """Package an application.

        :param app: The application to package
        :param sign_app: Should the application be signed? Default: ``True``
        :param identity: The code signing identity to use. This can be either
            the SHA-1 thumbprint for the cert, or filepath to the cert.
            Ignored if ``sign_app`` is ``False``.
        """

        if sign_app and not identity:
            sign_app = False

        if sign_app:
            self.logger.info("Signing App Binary", prefix=app.app_name)
            sign_options = self.get_signing_options(identity=identity)
            self.sign_file(
                app=app,
                filepath=self.binary_path(app),
                options=sign_options,
            )

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

        if sign_app:
            self.logger.info("Signing MSI", prefix=app.app_name)
            self.sign_file(
                app=app,
                filepath=self.distribution_path(app, packaging_format="msi"),
                options=sign_options,
            )
