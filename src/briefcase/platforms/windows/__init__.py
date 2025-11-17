from __future__ import annotations

import re
import subprocess
import uuid
from collections.abc import Collection
from pathlib import Path, PurePath
from zipfile import ZIP_DEFLATED, ZipFile

from briefcase.commands import CreateCommand, PackageCommand, RunCommand
from briefcase.config import AppConfig, parsed_version
from briefcase.exceptions import BriefcaseCommandError, UnsupportedHostError
from briefcase.integrations.windows_sdk import WindowsSDK
from briefcase.integrations.wix import WiX

DEFAULT_OUTPUT_FORMAT = "app"


def txt_to_rtf(txt):
    """A very simple TXT to RTF converter.

    The entire document is rendered in Courier. Any blank line is interpreted as a
    paragraph marker; any line starting with a * is rendered as a bullet. Everything
    else is rendered verbatim in the RTF document.

    :param text: The original text.
    :returns: The text in RTF format.
    """
    rtf = ["{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}}"]
    for line in txt.split("\n"):
        if line.lstrip().startswith("*"):
            rtf.append(f"\\bullet{line[line.index('*') + 1 :]} ")
        elif line:
            # Add a space at the end to ensure multi-line paragraphs
            # have a word break. Strip whitespace to ensure that
            # indented bullet paragraphs don't have extra space.
            rtf.append(line.strip() + " ")
        else:
            # A blank line is a paragraph+line break.
            rtf.append("\\par\\line")
    rtf.append("}")

    return "\n".join(rtf)


class WindowsMixin:
    platform = "windows"
    supported_host_os: Collection[str] = {"Windows"}
    supported_host_os_reason = "Windows applications can only be built on Windows."
    platform_target_version = "0.3.24"

    def bundle_package_executable_path(self, app):
        if app.console_app:
            return f"{app.app_name}.exe"
        else:
            return f"{app.formal_name}.exe"

    def bundle_package_path(self, app):
        return self.bundle_path(app) / self.packaging_root

    def binary_path(self, app):
        return self.package_path(app) / self.package_executable_path(app)

    def distribution_path(self, app):
        suffix = "zip" if app.packaging_format == "zip" else "msi"
        return self.dist_path / f"{app.formal_name}-{app.version}.{suffix}"

    def verify_host(self):
        super().verify_host()
        # The stub app only supports x86-64 right now, and our VisualStudio and WiX code
        # is the same (#1887). However, we can package an external x86-64 app on any
        # build machine.
        if self.tools.host_arch != "AMD64":
            if all(app.external_package_path for app in self.apps.values()):
                if not self.is_clone:
                    self.console.warning(
                        f"""
*************************************************************************
** WARNING: Possible architecture mismatch                             **
*************************************************************************

The build machine is {self.tools.host_arch}, but Briefcase on Windows currently only
supports x86-64 installers.

You are responsible for ensuring that the content of external_package_path
is compatible with x86-64.

*************************************************************************
"""
                    )
            else:
                raise UnsupportedHostError(
                    f"Windows applications cannot be built on an "
                    f"{self.tools.host_arch} machine."
                )

        # 64bit Python is required to ensure 64bit wheels are installed/created
        # for the app
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
        micro = re.match(r"\d+", str(support_revision)).group(0)
        return (
            f"https://www.python.org/ftp/python/"
            f"{self.python_version_tag}.{micro}/"
            f"{self.support_package_filename(support_revision)}"
        )

    def extras_path(self, app: AppConfig) -> Path:
        """Obtain the path for extra installer content.

        Extra installer content is content that needs to be inserted into the installer,
        in addition to material in the packaging path. It is primarily used to add
        installer scripts when packaging an externally managed app.

        :param app: The config object for the app
        :return: The full path where install scripts should be installed.
        """
        try:
            extras_path = self.path_index(app, "extras_path")
        except KeyError:
            # For backwards compatibility - if the template doesn't define an extras
            # path, default to `extras`.
            extras_path = "extras"

        return self.bundle_path(app) / extras_path

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
            self.console.info(f"Assigning {app.app_name} an application GUID of {guid}")

        try:
            install_scope = "perMachine" if app.system_installer else "perUser"
        except AttributeError:
            # system_installer not defined in config; default to asking the user
            install_scope = "perUserOrMachine"

        return {
            "version_triple": version_triple,
            "guid": str(guid),
            "install_scope": install_scope,
            "package_path": str(self.package_path(app)),
            "binary_path": self.package_executable_path(app),
        }

    def _cleanup_app_support_package(self, support_path):
        # On Windows, the support path is co-mingled with app content.
        # This means updating the support package is imperfect.
        # Warn the user that there could be problems.
        self.console.warning(
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

    def install_license(self, app: AppConfig):
        """Install the license for the project as RTF content.

        Currently assumes PEP621 format for `license`:
        * If `license.file` is an RTF file, it is used verbatim
        * If `license.file` is any other file, it is converted to RTF
          using a simple text->RTF conversion.
        * If `license.text` is provided, that text is converted to
          RTF; with a warning for the case where `license.text` is
          a one-line license name/description.

        If no `license` field is defined, or it points at a file that
        doesn't exist an error is raised.

        When PEP639 support is added, we will need to adapt this method.

        :param app: The config object for the app
        """
        installed_license = self.bundle_path(app) / "LICENSE.rtf"

        if license_file := app.license.get("file"):
            license_file = self.base_path / license_file
            if license_file.is_file():
                if license_file.suffix == ".rtf":
                    self.tools.shutil.copy(license_file, installed_license)
                    license_text = None
                else:
                    license_text = license_file.read_text(encoding="utf-8")
                    installed_license.write_text(
                        txt_to_rtf(license_text), encoding="utf-8"
                    )
            else:
                raise BriefcaseCommandError(
                    f"Your `pyproject.toml` specifies a license file of "
                    f"{str(license_file.relative_to(self.base_path))!r}.\n"
                    f"However, this file does not exist."
                    f"\n\n"
                    "Ensure you have correctly spelled the filename in your "
                    "`license.file` setting."
                )
        elif license_text := app.license.get("text"):
            if len(license_text.splitlines()) <= 1:
                self.console.warning(
                    """
Your app specifies a license using `license.text`, but the value doesn't appear
to be a full license. Briefcase will generate a `LICENSE.rtf` file for your
project; you should ensure that the contents of this file is adequate.
"""
                )
            installed_license.write_text(
                txt_to_rtf(license_text),
                encoding="utf-8",
            )
        else:
            raise BriefcaseCommandError(
                """\
Your project does not contain a `license` definition.

Create a file named `LICENSE` in the same directory as your `pyproject.toml`
with your app's licensing terms, and set `license.file = 'LICENSE'` in your
app's configuration.
"""
            )

    def install_app_resources(self, app: AppConfig):
        """Install Windows-specific app resources.

        This includes any post-install or pre-uninstall scripts, plus converting the
        LICENSE file into an RTF file.

        :param app: The config object for the app
        """
        super().install_app_resources(app)

        installer_path = getattr(app, "installer_path", "_installer")
        install_scripts_path = self.extras_path(app) / installer_path

        # Ensure the extras path exists, so that the path used by WiX exists
        self.extras_path(app).mkdir(exist_ok=True, parents=True)

        # Install the post-install script
        if post_install := getattr(app, "post_install_script", None):
            post_install_script = self.base_path / post_install
            if post_install_script.suffix != ".bat":
                raise BriefcaseCommandError(
                    "Windows post-install scripts must be .bat files."
                )
            elif not post_install_script.is_file():
                raise BriefcaseCommandError(
                    f"Couldn't find post-install script {post_install}."
                )

            with self.console.wait_bar("Installing post-install script..."):
                install_scripts_path.mkdir(exist_ok=True, parents=True)
                self.tools.shutil.copyfile(
                    post_install_script,
                    install_scripts_path / "post_install.bat",
                )

        # Install the pre-uninstall script
        if pre_uninstall := getattr(app, "pre_uninstall_script", None):
            pre_uninstall_script = self.base_path / pre_uninstall
            if pre_uninstall_script.suffix != ".bat":
                raise BriefcaseCommandError(
                    "Windows pre-uninstall scripts must be .bat files."
                )
            elif not pre_uninstall_script.is_file():
                raise BriefcaseCommandError(
                    f"Couldn't find pre-uninstall script {pre_uninstall}."
                )

            with self.console.wait_bar("Installing pre-uninstall script..."):
                install_scripts_path.mkdir(exist_ok=True, parents=True)
                self.tools.shutil.copyfile(
                    pre_uninstall_script,
                    install_scripts_path / "pre_uninstall.bat",
                )

        # Install the license.
        with self.console.wait_bar("Installing license..."):
            self.install_license(app)


class WindowsRunCommand(RunCommand):
    supports_debugger = True

    def run_app(
        self,
        app: AppConfig,
        passthrough: list[str],
        **kwargs,
    ):
        """Start the application.

        :param app: The config object for the app
        :param passthrough: The list of arguments to pass to the app
        """
        # Set up the log stream
        kwargs = self._prepare_app_kwargs(app=app)

        # Console apps must operate in non-streaming mode so that console input can
        # be handled correctly. However, if we're in test mode, we *must* stream so
        # that we can see the test exit sentinel
        if app.console_app and not app.test_mode:
            self.console.info("=" * 75)
            self.tools.subprocess.run(
                [self.binary_path(app), *passthrough],
                cwd=self.tools.home_path,
                encoding="UTF-8",
                bufsize=1,
                stream_output=False,
                **kwargs,
            )
        else:
            # Start the app in a way that lets us stream the logs
            app_popen = self.tools.subprocess.Popen(
                [self.binary_path(app), *passthrough],
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
                "Specifies the code signing certificate is stored in the "
                "Local Machine's stores instead of the Current User's"
            ),
            action="store_true",
            dest="use_local_machine",
            required=False,
        )
        parser.add_argument(
            "--cert-store",
            help=(
                "The internal Windows name for the certificate store containing the "
                "certificate for code signing; defaults to 'My' for the Personal store"
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
                f"Codesigning identify {identity!r} must be a "
                f"certificate SHA-1 thumbprint."
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
        identity: str | None = None,
        adhoc_sign: bool = False,
        file_digest: str | None = None,
        use_local_machine: bool = False,
        cert_store: str | None = None,
        timestamp_url: str | None = None,
        timestamp_digest: str | None = None,
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
            self.console.warning(
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
            self.console.info("Signing App...", prefix=app.app_name)
            sign_options = {
                "identity": identity,
                "file_digest": file_digest,
                "use_local_machine": use_local_machine,
                "cert_store": cert_store,
                "timestamp_url": timestamp_url,
                "timestamp_digest": timestamp_digest,
            }
            self.sign_file(app=app, filepath=self.binary_path(app), **sign_options)

        if app.packaging_format == "zip":
            self._package_zip(app)
        else:
            self._package_msi(app)

            if sign_app:
                self.console.info("Signing MSI...", prefix=app.app_name)
                self.sign_file(
                    app=app,
                    filepath=self.distribution_path(app),
                    **sign_options,
                )

    def _package_msi(self, app):
        """Build the msi installer."""
        try:
            with self.console.wait_bar("Building MSI..."):
                self.tools.subprocess.run(
                    [
                        self.tools.wix.wix_exe,
                        "build",
                        "-ext",
                        self.tools.wix.ext_path("UI"),
                        "-arch",
                        "x64",  # Default is x86, regardless of the build machine.
                        f"{app.app_name}.wxs",
                        "-loc",
                        "unicode.wxl",
                        "-pdbtype",
                        "none",
                        "-o",
                        self.distribution_path(app),
                    ],
                    check=True,
                    cwd=self.bundle_path(app),
                )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to package app {app.app_name}.") from e

    def _package_zip(self, app):
        """Package the app as simple zip file."""

        self.console.info("Building zip file...", prefix=app.app_name)
        with self.console.wait_bar("Packing..."):
            source = self.package_path(app)
            zip_root = f"{app.formal_name}-{app.version}"

            with ZipFile(self.distribution_path(app), "w", ZIP_DEFLATED) as archive:
                for file_path in source.glob("**/*"):
                    archive.write(
                        file_path, zip_root / PurePath(file_path).relative_to(source)
                    )
