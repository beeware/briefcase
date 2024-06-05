import re
import subprocess
import uuid
from pathlib import Path, PurePath
from typing import List
from zipfile import ZIP_DEFLATED, ZipFile

from briefcase.commands import CreateCommand, PackageCommand, RunCommand
from briefcase.config import AppConfig, parsed_version
from briefcase.exceptions import BriefcaseCommandError, UnsupportedHostError
from briefcase.integrations.windows_sdk import WindowsSDK
from briefcase.integrations.wix import WiX

DEFAULT_OUTPUT_FORMAT = "app"


class WindowsMixin:
    platform = "windows"
    supported_host_os = {"Windows"}
    supported_host_os_reason = "Windows applications can only be built on Windows."

    def binary_path(self, app):
        if app.console_app:
            return self.bundle_path(app) / self.packaging_root / f"{app.app_name}.exe"
        else:
            return (
                self.bundle_path(app) / self.packaging_root / f"{app.formal_name}.exe"
            )

    def distribution_path(self, app):
        suffix = "zip" if app.packaging_format == "zip" else "msi"
        return self.dist_path / f"{app.formal_name}-{app.version}.{suffix}"

    def verify_host(self):
        super().verify_host()
        # the stub app only supports x86-64 right now
        if self.tools.host_arch != "AMD64":
            raise UnsupportedHostError(
                f"Windows applications cannot be built on an {self.tools.host_arch} machine."
            )
        # 64bit Python is required to ensure 64bit wheels are installed/created for the app
        if self.tools.is_32bit_python:
            raise UnsupportedHostError(
                """\
Windows applications cannot be built using a 32bit version of Python.

Install a 64bit version of Python and run Briefcase again.
"""
            )


class WindowsCreateCommand(CreateCommand):
    def support_package_filename(self, support_revision):
        return f"python-{self.python_version_tag}.{support_revision}-embed-amd64.zip"

    def support_package_url(self, support_revision):
        return (
            f"https://www.python.org/ftp/python/"
            f"{self.python_version_tag}.{support_revision}/"
            f"{self.support_package_filename(support_revision)}"
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
            domain = ".".join(app.bundle_identifier.split(".")[::-1])
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

    def _cleanup_app_support_package(self, support_path):
        # On Windows, the support path is co-mingled with app content.
        # This means updating the support package is imperfect.
        # Warn the user that there could be problems.
        self.logger.warning(
            """
*************************************************************************
** WARNING: Support package update may be imperfect                    **
*************************************************************************

    Support packages in Windows apps are overlaid with app content,
    so it isn't possible to remove all old support files before
    installing new ones.

    Briefcase will unpack the new support package without cleaning up
    existing support package content. This *should* work; however,
    ensure a reproducible release artefacts, it is advisable to
    perform a clean app build before release.

*************************************************************************
"""
        )


class WindowsRunCommand(RunCommand):
    def run_app(
        self,
        app: AppConfig,
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
        kwargs = self._prepare_app_kwargs(app=app, test_mode=test_mode)

        # Console apps must operate in non-streaming mode so that console input can
        # be handled correctly. However, if we're in test mode, we *must* stream so
        # that we can see the test exit sentinel
        if app.console_app and not test_mode:
            self.logger.info("=" * 75)
            self.tools.subprocess.run(
                [self.binary_path(app)] + passthrough,
                cwd=self.tools.home_path,
                encoding="UTF-8",
                bufsize=1,
                stream_output=False,
                **kwargs,
            )
        else:
            # Start the app in a way that lets us stream the logs
            app_popen = self.tools.subprocess.Popen(
                [self.binary_path(app)] + passthrough,
                cwd=self.tools.home_path,
                encoding="UTF-8",
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
    ADHOC_SIGN_HELP = (
        "Perform no signing on the app. "
        "Your app will be reported as coming from an unverified publisher."
    )

    IDENTITY_HELP = "The 40-digit hex checksum of the code signing identity to use"

    @property
    def packaging_formats(self):
        return ["msi", "zip"]

    @property
    def default_packaging_format(self):
        return "msi"

    def verify_tools(self):
        super().verify_tools()
        WiX.verify(tools=self.tools)
        if self._windows_sdk_needed:
            WindowsSDK.verify(tools=self.tools)

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "--file-digest",
            help="File digest algorithm to use for code signing; defaults to sha256",
            default="sha256",
            required=False,
        )
        parser.add_argument(
            "--use-local-machine-stores",
            help=(
                "Specifies the code signing certificate is stored in the Local Machine's "
                "stores instead of the Current User's"
            ),
            action="store_true",
            dest="use_local_machine",
            required=False,
        )
        parser.add_argument(
            "--cert-store",
            help=(
                "The internal Windows name for the certificate store containing the certificate "
                "for code signing; defaults to 'My' for the Personal store"
            ),
            default="My",
            required=False,
        )
        parser.add_argument(
            "--timestamp-url",
            help=(
                "URL for the Timestamp Authority server to timestamp the code signing; "
                "defaults to timestamp.digicert.com"
            ),
            default="http://timestamp.digicert.com",
            required=False,
        )
        parser.add_argument(
            "--timestamp-digest",
            help=(
                "Digest algorithm to request the Timestamp Authority server uses "
                "for the timestamp for code signing; defaults to sha256"
            ),
            default="sha256",
            required=False,
        )

    def parse_options(self, extra):
        """Require the Windows SDK tool if an `identity` is specified for signing."""
        options, overrides = super().parse_options(extra=extra)
        self._windows_sdk_needed = options["identity"] is not None
        return options, overrides

    def sign_file(
        self,
        app: AppConfig,
        filepath: Path,
        identity: str,
        file_digest: str,
        use_local_machine: bool,
        cert_store: str,
        timestamp_url: str,
        timestamp_digest: str,
    ):
        """Sign a file."""

        if not re.fullmatch(r"^[0-9a-f]{40}$", identity, flags=re.IGNORECASE):
            raise BriefcaseCommandError(
                f"Codesigning identify {identity!r} must be a certificate SHA-1 thumbprint."
            )

        sign_command = [
            self.tools.windows_sdk.signtool_exe,
            "sign",
            "-s",
            cert_store,
            "-sha1",
            identity,
            "-fd",
            file_digest,
            "-d",
            app.description,
            "-du",
            app.url,
            "-tr",
            timestamp_url,
            "-td",
            timestamp_digest,
        ]

        if use_local_machine:
            # Look for cert in Local Machine instead of Current User
            sign_command.append("-sm")

        # Filepath to sign must come last
        sign_command.append(filepath)

        try:
            self.tools.subprocess.run(sign_command, check=True)
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to sign {filepath}") from e

    def package_app(
        self,
        app: AppConfig,
        identity: str = None,
        adhoc_sign: bool = False,
        file_digest: str = None,
        use_local_machine: bool = False,
        cert_store: str = None,
        timestamp_url: str = None,
        timestamp_digest: str = None,
        **kwargs,
    ):
        """Package an application.

        Code signing parameters are ignored if ``sign_app=False``. If a code signing
        identity is not provided, then ``sign_app=False`` will be enforced.

        :param app: The application to package
        :param identity: SHA-1 thumbprint of the certificate to use for code signing.
        :param adhoc_sign: Should the application be signed? Default: ``True``
        :param file_digest: File hashing algorithm for code signing.
        :param use_local_machine: True to use cert stores for the Local Machine instead
            of the Current User; default to False for Current User.
        :param cert_store: Certificate store within Current User or Local Machine to
            search for the certificate within.
        :param timestamp_url: Timestamp authority server to use in code signing.
        :param timestamp_digest: Hashing algorithm to request from the timestamp server.
        """

        if adhoc_sign:
            sign_app = False
        elif identity:
            sign_app = True
        else:
            sign_app = False
            self.logger.warning(
                """
*************************************************************************
** WARNING: No signing identity provided                               **
*************************************************************************

    Briefcase will not sign the app. To provide a signing identity,
    use the `--identity` option; or, to explicitly disable signing,
    use `--adhoc-sign`.

*************************************************************************
"""
            )

        if sign_app:
            self.logger.info("Signing App...", prefix=app.app_name)
            sign_options = dict(
                identity=identity,
                file_digest=file_digest,
                use_local_machine=use_local_machine,
                cert_store=cert_store,
                timestamp_url=timestamp_url,
                timestamp_digest=timestamp_digest,
            )
            self.sign_file(app=app, filepath=self.binary_path(app), **sign_options)

        if app.packaging_format == "zip":
            self._package_zip(app)
        else:
            self._package_msi(app)

            if sign_app:
                self.logger.info("Signing MSI...", prefix=app.app_name)
                self.sign_file(
                    app=app,
                    filepath=self.distribution_path(app),
                    **sign_options,
                )

    def _package_msi(self, app):
        """Build the msi installer."""

        self.logger.info("Building MSI...", prefix=app.app_name)
        try:
            self.logger.info("Compiling application manifest...")
            with self.input.wait_bar("Compiling..."):
                self.tools.subprocess.run(
                    [
                        self.tools.wix.heat_exe,
                        "dir",
                        self.packaging_root,
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
                        self.distribution_path(app),
                        f"{app.app_name}.wixobj",
                        f"{app.app_name}-manifest.wixobj",
                    ],
                    check=True,
                    cwd=self.bundle_path(app),
                )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to link app {app.app_name}.") from e

    def _package_zip(self, app):
        """Package the app as simple zip file."""

        self.logger.info("Building zip file...", prefix=app.app_name)
        with self.input.wait_bar("Packing..."):
            source = self.bundle_path(app) / self.packaging_root  # /src
            zip_root = f"{app.formal_name}-{app.version}"

            with ZipFile(self.distribution_path(app), "w", ZIP_DEFLATED) as archive:
                for file_path in source.glob("**/*"):
                    archive.write(
                        file_path, zip_root / PurePath(file_path).relative_to(source)
                    )
