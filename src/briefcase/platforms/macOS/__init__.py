from __future__ import annotations

import concurrent.futures
import os
import plistlib
import re
import subprocess
import time
from contextlib import suppress
from pathlib import Path
from signal import SIGTERM

from briefcase.config import AppConfig
from briefcase.console import select_option
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import get_process_id_by_command, is_process_dead
from briefcase.integrations.xcode import XcodeCliTools, get_identities
from briefcase.platforms.macOS.filters import macOS_log_clean_filter
from briefcase.platforms.macOS.utils import AppPackagesMergeMixin

try:
    import dmgbuild
except ImportError:  # pragma: no-cover-if-is-macos
    # On non-macOS platforms, dmgbuild won't be installed.
    # Allow the plugin to be loaded; raise an error when tools are verified.
    dmgbuild = None


DEFAULT_OUTPUT_FORMAT = "app"

ADHOC_IDENTITY_NAME = (
    "Ad-hoc identity. The resulting package will run but cannot be re-distributed."
)


class SigningIdentity:
    def __init__(self, id="-", name=None):
        """A wrapper around the various forms of an Apple signing identity."""
        self.id = id
        if self.id == "-":
            self.team_id = None
            self.name = ADHOC_IDENTITY_NAME
        else:
            self.name = name
            self.team_id = self.team_id_from_name(name)

    @classmethod
    def team_id_from_name(cls, name):
        try:
            return re.match(r".*\(([\dA-Z]*)\)", name)[1]
        except TypeError:
            raise BriefcaseCommandError(
                f"Couldn't extract Team ID from signing identity {name!r}"
            )

    @property
    def is_adhoc(self):
        """Is this the adhoc identity?"""
        return self.id == "-"

    def __repr__(self):
        if self.is_adhoc:
            return "<AdhocSigningIdentity>"
        else:
            return f"<SigningIdentity id={self.id}>"

    def __eq__(self, other):
        return isinstance(other, SigningIdentity) and self.id == other.id


class macOSMixin:
    platform = "macOS"
    supported_host_os = {"Darwin"}
    supported_host_os_reason = "macOS applications can only be built on macOS."
    # 0.3.20 introduced a framework-based support package.
    platform_target_version = "0.3.20"


class macOSCreateMixin(AppPackagesMergeMixin):
    hidden_app_properties = {"permission", "entitlement"}

    def _install_app_requirements(
        self,
        app: AppConfig,
        requires: list[str],
        app_packages_path: Path,
    ):
        if getattr(app, "universal_build", True):
            # Perform the initial install targeting the current platform
            host_app_packages_path = (
                self.bundle_path(app) / f"app_packages.{self.tools.host_arch}"
            )
            super()._install_app_requirements(
                app,
                requires=requires,
                app_packages_path=host_app_packages_path,
            )

            # Find all the packages with binary components.
            # We can ignore any -universal2 packages; they're already fat.
            binary_packages = self.find_binary_packages(
                host_app_packages_path,
                universal_suffix="_universal2",
            )

            # Now install dependencies for the architecture that isn't the host architecture.
            other_arch = {
                "arm64": "x86_64",
                "x86_64": "arm64",
            }[self.tools.host_arch]

            # Create a temporary folder targeting the other platform
            other_app_packages_path = (
                self.bundle_path(app) / f"app_packages.{other_arch}"
            )
            if other_app_packages_path.is_dir():
                self.tools.shutil.rmtree(other_app_packages_path)
            self.tools.os.mkdir(other_app_packages_path)

            if binary_packages:
                with self.input.wait_bar(
                    f"Installing binary app requirements for {other_arch}..."
                ):
                    self._pip_install(
                        app,
                        app_packages_path=other_app_packages_path,
                        pip_args=[
                            "--no-deps",
                            "--only-binary",
                            ":all:",
                        ]
                        + [
                            f"{package}=={version}"
                            for package, version in binary_packages
                        ],
                        install_hint=f"""

If an {other_arch} wheel has not been published for one or more of your requirements,
you must compile those wheels yourself, or build a non-universal app by setting:

    universal_build = False

in the macOS configuration section of your pyproject.toml.
""",
                        env={
                            "PYTHONPATH": str(
                                self.support_path(app)
                                / "platform-site"
                                / f"macosx.{other_arch}"
                            )
                        },
                    )
            else:
                self.logger.info("All packages are pure Python, or universal.")

            # If given the option of a single architecture binary or a universal2 binary,
            # pip will install the single platform binary. However, a common situation on
            # macOS is for there to be an x86_64 binary and a universal2 binary. This means
            # you only get a universal2 binary in the "other" install pass. This then causes
            # problems with merging, because the "other" binary contains a copy of the
            # architecture that the "host" platform provides.
            #
            # To avoid this - ensure that the libraries in the app packages for the "other"
            # arch are all thin.
            #
            # This doesn't matter if it happens the other way around - if the "host" arch
            # installs a universal binary, then the "other" arch won't be asked to install
            # a binary at all.
            self.thin_app_packages(other_app_packages_path, arch=other_arch)

            # Merge the binaries
            self.merge_app_packages(
                target_app_packages=app_packages_path,
                sources=[host_app_packages_path, other_app_packages_path],
            )
        else:
            # If we're not building a universal binary, we can do a single install pass
            # directly into the app_packages folder.
            super()._install_app_requirements(
                app,
                requires=requires,
                app_packages_path=app_packages_path,
            )

            # Since we're only targeting 1 architecture, we can strip any universal
            # libraries down to just the host architecture.
            self.thin_app_packages(app_packages_path, arch=self.tools.host_arch)

    def permissions_context(self, app: AppConfig, cross_platform: dict[str, str]):
        """Additional template context for permissions.

        :param app: The config object for the app
        :param cross_platform: The dictionary of known cross-platform permission
            definitions.
        :returns: The template context describing permissions for the app.
        """
        # The info.plist entries for the app
        info = {}

        # Default entitlements for all macOS apps
        entitlements = {
            "com.apple.security.cs.allow-unsigned-executable-memory": True,
            "com.apple.security.cs.disable-library-validation": True,
        }

        if cross_platform["camera"]:
            entitlements["com.apple.security.device.camera"] = True
            info["NSCameraUsageDescription"] = cross_platform["camera"]
        if cross_platform["microphone"]:
            entitlements["com.apple.security.device.microphone"] = True
            info["NSMicrophoneUsageDescription"] = cross_platform["microphone"]

        if cross_platform["background_location"]:
            info["NSLocationUsageDescription"] = cross_platform["background_location"]
            entitlements["com.apple.security.personal-information.location"] = True
        elif cross_platform["fine_location"]:
            info["NSLocationUsageDescription"] = cross_platform["fine_location"]
            entitlements["com.apple.security.personal-information.location"] = True
        elif cross_platform["coarse_location"]:
            info["NSLocationUsageDescription"] = cross_platform["coarse_location"]
            entitlements["com.apple.security.personal-information.location"] = True

        if cross_platform["photo_library"]:
            info["NSPhotoLibraryUsageDescription"] = cross_platform["photo_library"]
            entitlements["com.apple.security.personal-information.photo_library"] = True

        # Override any info and entitlement definitions with the platform specific definitions
        info.update(getattr(app, "info", {}))
        entitlements.update(getattr(app, "entitlement", {}))

        return {
            "info": info,
            "entitlements": entitlements,
        }


class macOSRunMixin:
    def run_app(
        self,
        app: AppConfig,
        test_mode: bool,
        passthrough: list[str],
        **kwargs,
    ):
        """Start the application.

        :param app: The config object for the app
        :param test_mode: Boolean; Is the app running in test mode?
        :param passthrough: The list of arguments to pass to the app
        """
        # Console apps must operate in non-streaming mode so that console input can
        # be handled correctly. However, if we're in test mode, we *must* stream so
        # that we can see the test exit sentinel.
        if app.console_app:
            self.run_console_app(
                app,
                test_mode=test_mode,
                passthrough=passthrough,
                **kwargs,
            )
        else:
            self.run_gui_app(
                app,
                test_mode=test_mode,
                passthrough=passthrough,
                **kwargs,
            )

    def run_console_app(
        self,
        app: AppConfig,
        test_mode: bool,
        passthrough: list[str],
        **kwargs,
    ):
        """Start the console application.

        :param app: The config object for the app
        :param test_mode: Boolean; Is the app running in test mode?
        :param passthrough: The list of arguments to pass to the app
        """
        sub_kwargs = self._prepare_app_kwargs(app=app, test_mode=test_mode)
        cmdline = [self.binary_path(app) / f"Contents/MacOS/{app.formal_name}"]
        cmdline.extend(passthrough)

        if test_mode:
            # Stream the app's output for testing.
            # When a console app runs normally, its stdout should be connected
            # directly to the terminal to properly display the app. When its test
            # suite is running, though, Briefcase should stream the output to
            # capture the testing outcome.
            app_popen = self.tools.subprocess.Popen(
                cmdline,
                cwd=self.tools.home_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                **sub_kwargs,
            )
            self._stream_app_logs(app, popen=app_popen, test_mode=test_mode)

        else:
            try:
                # Start the app directly
                self.logger.info("=" * 75)
                self.tools.subprocess.run(
                    cmdline,
                    cwd=self.tools.home_path,
                    check=True,
                    stream_output=False,
                    **sub_kwargs,
                )
            except subprocess.CalledProcessError:
                # The command line app *could* returns an error code, which is entirely legal.
                # Ignore any subprocess error here.
                pass

    def run_gui_app(
        self,
        app: AppConfig,
        test_mode: bool,
        passthrough: list[str],
        **kwargs,
    ):
        """Start the GUI application.

        :param app: The config object for the app
        :param test_mode: Boolean; Is the app running in test mode?
        :param passthrough: The list of arguments to pass to the app
        """
        # Start log stream for the app.
        # Streaming the system log is... a mess. The system log contains a
        # *lot* of noise from other processes; even if you filter by
        # process, there's a lot of macOS-generated noise. It's very
        # difficult to extract just the "user generated" stdout/err log
        # messages.
        #
        # The following sets up a log stream filter that looks for:
        #  1. a log sender that matches that app binary; or,
        #  2. a log sender of libffi, and a process that matches the app binary.
        # Case (1) works for pre-Python 3.9 static linked binaries.
        # Case (2) works for Python 3.9+ dynamic linked binaries.
        # It's not enough to filter on *just* the processImagePath,
        # as the process will generate lots of system-level messages.
        # We can't filter on *just* the senderImagePath, because other
        # apps will generate log messages that would be caught by the filter.
        sender = os.fsdecode(self.binary_path(app) / "Contents/MacOS" / app.formal_name)
        log_popen = self.tools.subprocess.Popen(
            [
                "log",
                "stream",
                "--style",
                "compact",
                "--predicate",
                f'senderImagePath=="{sender}"'
                f' OR (processImagePath=="{sender}"'
                ' AND senderImagePath=="/usr/lib/libffi.dylib")',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )

        # Wait for the log stream start up
        time.sleep(0.25)

        app_pid = None
        try:
            # Set up the log stream
            sub_kwargs = self._prepare_app_kwargs(app=app, test_mode=test_mode)

            # Start the app in a way that lets us stream the logs
            self.tools.subprocess.run(
                # Force a new app to be launched
                ["open", "-n", self.binary_path(app)]
                + ((["--args"] + passthrough) if passthrough else []),
                cwd=self.tools.home_path,
                check=True,
                **sub_kwargs,
            )

            # Find the App process ID so log streaming can exit when the app exits
            app_pid = get_process_id_by_command(
                command=str(self.binary_path(app)),
                logger=self.logger,
            )

            if app_pid is None:
                raise BriefcaseCommandError(
                    f"Unable to find process for app {app.app_name} to start log streaming."
                )

            # Stream the app logs.
            self._stream_app_logs(
                app,
                popen=log_popen,
                test_mode=test_mode,
                clean_filter=macOS_log_clean_filter,
                clean_output=True,
                stop_func=lambda: is_process_dead(app_pid),
                log_stream=True,
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(f"Unable to start app {app.app_name}.")
        finally:
            # Ensure the App also terminates when exiting
            if app_pid:  # pragma: no-cover-if-is-py310
                with suppress(ProcessLookupError):
                    self.tools.os.kill(app_pid, SIGTERM)


def is_mach_o_binary(path):  # pragma: no-cover-if-is-windows
    """Determine if the file at the given path is a Mach-O binary.

    :param path: The path to check
    :returns: True if the file at the given location is a Mach-O binary.
    """
    # A binary is any file that is executable, or has a suffix from a known list
    if os.access(path, os.X_OK) or path.suffix.lower() in {".dylib", ".o", ".so", ""}:
        # File is a binary; read the file magic to determine if it's Mach-O.
        with path.open("rb") as f:
            magic = f.read(4)
            return magic in (
                b"\xCA\xFE\xBA\xBE",
                b"\xCF\xFA\xED\xFE",
                b"\xCE\xFA\xED\xFE",
                b"\xBE\xBA\xFE\xCA",
                b"\xFE\xED\xFA\xCF",
                b"\xFE\xED\xFA\xCE",
            )
    else:
        # Not a binary
        return False


class macOSSigningMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External service APIs.
        # These are abstracted to enable testing without patching.
        self.get_identities = get_identities

    def entitlements_path(self, app: AppConfig):  # pragma: no-cover-if-is-windows
        return self.bundle_path(app) / self.path_index(app, "entitlements_path")

    def select_identity(
        self,
        identity: str | None = None,
        app_identity: SigningIdentity | None = None,
    ) -> SigningIdentity:
        """Get the codesigning identity to use.

        This can be either an application codesigning identity, or an installer
        identity. An installer identity must be from the same Team ID as the application
        identity.

        :param identity: A pre-specified identity (either the 40-digit hex checksum, or
            the string name of the identity). If provided, it will be validated against
            the list of available identities to confirm that it is a valid codesigning
            identity.
        :param app_identity: The application signing identity to match when producing an
            installer identity. Only non-app signing identities that match the team ID
            for the ``app_identity`` will be presented as options. Omit this value to
            select an app signing identity.
        :returns: The final identity to use
        """
        # Obtain the valid codesigning identities. These are the identities that could
        # be used for app signing.
        identities = self.get_identities(self.tools, "codesigning")

        if app_identity:
            ident_type = "installer"
            ident_option = "--installer-identity"
            # There's no way to explicitly request a list of installer identities. As a
            # workaround, get the full, unfiltered list of all signing identities; then
            # remove any identity that:
            # 1. From a different team to the provided app identity; or
            # 2. Appears on the list of app signing identities.
            app_identities = identities
            identities = {
                key: name
                for key, name in self.get_identities(self.tools).items()
                if SigningIdentity.team_id_from_name(name) == app_identity.team_id
                and key not in app_identities
            }

            if not identities:
                raise BriefcaseCommandError(
                    f"No installer signing identities for team {app_identity.team_id} could be found."
                )
        else:
            ident_type = "application"
            ident_option = "--identity"

            # App signing also allows for the adhoc identity
            identities["-"] = ADHOC_IDENTITY_NAME

        if identity:
            try:
                # Try to look up the identity as a hex checksum
                identity_name = identities[identity]
                return SigningIdentity(id=identity, name=identity_name)
            except KeyError as e:
                # Try to look up the identity as readable name
                try:
                    reverse_lookup = {name: ident for ident, name in identities.items()}
                    identity_id = reverse_lookup[identity]
                    return SigningIdentity(id=identity_id, name=identity)
                except KeyError:
                    # Not found as an ID or name
                    raise BriefcaseCommandError(
                        f"Invalid {ident_type} signing identity {identity}"
                    ) from e

        self.input.prompt()
        self.input.prompt(f"Select {ident_type} signing identity to use:")
        self.input.prompt()
        identity = select_option(identities, input=self.input)
        identity_name = identities[identity]
        if identity == "-":
            self.logger.info(
                f"""
In the future, you could specify this signing identity by running:

    $ briefcase {self.command} macOS --adhoc-sign

"""
            )
        else:
            self.logger.info(
                f"""
In the future, you could specify this signing identity by running:

    $ briefcase {self.command} macOS {ident_option} {identity}

or

    $ briefcase {self.command} macOS {ident_option} "{identity_name}"

"""
            )

        return SigningIdentity(id=identity, name=identity_name)

    def sign_file(
        self,
        path: Path,
        identity: SigningIdentity,
        entitlements: Path | None = None,
    ):
        """Code sign a file.

        :param path: The path to the file to sign.
        :param identity: The code signing identity to use.
        :param entitlements: The path to the entitlements file to use.
        """
        options = "runtime" if not identity.is_adhoc else None
        process_command = ["codesign", path, "--sign", identity.id, "--force"]

        if entitlements:
            process_command.append("--entitlements")
            process_command.append(entitlements)
        if options:
            process_command.append("--options")
            process_command.append(options)

        self.logger.verbose(f"Signing {Path(path).relative_to(self.base_path)}")

        try:
            self.tools.subprocess.run(
                process_command,
                stderr=subprocess.PIPE,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            errors = e.stderr
            if any(
                msg in errors
                for msg in [
                    # File has a signature matching the Mach-O magic,
                    # but isn't actually a Mach-O binary
                    "unsupported format for signature",
                    # A folder named ``.framework`, but not actually a macOS Framework`
                    "bundle format unrecognized, invalid, or unsuitable",
                ]
            ):
                # We should not be signing this in the first place
                self.logger.verbose(
                    f"... {Path(path).relative_to(self.base_path)} does not require a signature"
                )
                return
            else:
                raise BriefcaseCommandError(f"Unable to code sign {path}.")

    def sign_app(
        self,
        app: AppConfig,
        identity: SigningIdentity,
    ):  # pragma: no-cover-if-is-windows
        """Sign an entire app with a specific identity.

        :param app: The app to sign
        :param identity: The signing identity to use
        """
        bundle_path = self.binary_path(app)
        resources_path = bundle_path / "Contents/Resources"
        frameworks_path = bundle_path / "Contents/Frameworks"

        sign_targets = []

        for folder in (resources_path, frameworks_path):
            # Sign all Mach-O executable objects
            sign_targets.extend(
                path
                for path in folder.rglob("*")
                if not path.is_dir()
                and not path.is_symlink()
                and is_mach_o_binary(path)
            )

            # Sign all embedded frameworks
            sign_targets.extend(folder.rglob("*.framework"))

            # Sign all embedded app objects
            sign_targets.extend(folder.rglob("*.app"))

        # Sign the bundle path itself
        sign_targets.append(bundle_path)

        # Run signing through a ThreadPoolExecutor so that they run in parallel. We need
        # to ensure that objects are signed from the inside out (i.e., a folder must be
        # signed *after* all it's contents has been signed; files in a folder must be
        # signed *after* all subfolders in that same folder); and an app that uses a
        # library must be signed *after* all the libraries it uses. See
        # https://developer.apple.com/documentation/xcode/creating-distribution-signed-code-for-the-mac#Determine-the-signing-order
        # for details.
        #
        # To do this, we utilize grouping on a sorted list, and rely on the fact that a
        # new group is created whenever the grouping key changes. The sorting process
        # guarantees depth-first ordering; the grouping is applied over the sorted
        # content, ensuring that that folders are signed before files.
        #
        # This approach isn't perfect. It will fail if there's an embedded app that uses
        # a library in a different framework, and the app is lexically sorted before the
        # library (e.g. if app_packages/foobar/Alpha.framework/Helpers/My App.app
        # depends on app_packages/footbar/Beta.framework/libbeta). However, if you're
        # embedding apps in frameworks in Python libraries that are installed by pip,
        # you're already making poor life choices; this approach is enough to satisfy
        # the one use of app-in-framework embedding that we're aware of (PySide).
        progress_bar = self.input.progress_bar()
        task_id = progress_bar.add_task("Signing App", total=len(sign_targets))
        with progress_bar:
            for group in self.tools.file.sorted_depth_first_groups(sign_targets):
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    for path in group:
                        future = executor.submit(
                            self.sign_file,
                            path,
                            entitlements=self.entitlements_path(app),
                            identity=identity,
                        )
                        futures.append(future)
                    for future in concurrent.futures.as_completed(futures):
                        progress_bar.update(task_id, advance=1)
                        if future.exception():
                            raise future.exception()


class macOSPackageMixin(macOSSigningMixin):
    ADHOC_SIGN_HELP = (
        "Perform ad-hoc signing on the app. "
        "The app will only run on this machine; it cannot be redistributed to others"
    )
    IDENTITY_HELP = (
        "The code signing identity to use; either the 40-digit hex "
        "checksum, or the full name of the identity"
    )

    @property
    def packaging_formats(self):
        return ["zip", "dmg", "pkg"]

    @property
    def default_packaging_format(self):
        # The default changes depending on whether the app is a console app or a GUI app
        return None

    def distribution_path(self, app):
        if app.packaging_format == "zip":
            return self.dist_path / f"{app.formal_name}-{app.version}.app.zip"
        elif app.packaging_format == "pkg":
            return self.dist_path / f"{app.formal_name}-{app.version}.pkg"
        else:
            return self.dist_path / f"{app.formal_name}-{app.version}.dmg"

    def add_options(self, parser):
        super().add_options(parser)

        # --no-sign-installer and --installer-identity are mutually exclusive
        installer_signing_group = parser.add_mutually_exclusive_group()
        installer_signing_group.add_argument(
            "--no-sign-installer",
            dest="sign_installer",
            help="Do not sign the installer. Ignored unless using PKG format",
            action="store_false",
        )
        installer_signing_group.add_argument(
            "--installer-identity",
            dest="installer_identity",
            help=(
                "The code signing identity to use for signing the installer. "
                "Ignored unless using PKG format"
            ),
            required=False,
        )

        # We use store_const:False rather than store_false so that the
        # "unspecified" value is None, rather than True, allowing for
        # a "default behavior" interpretation when `--adhoc-sign` is specified
        parser.add_argument(
            "--no-notarize",
            dest="notarize_app",
            action="store_const",
            const=False,
            help="Disable notarization for the app",
        )

    def verify_tools(self):
        # Require the Xcode command line tools.
        XcodeCliTools.verify(tools=self.tools)

        # Verify superclass tools *after* xcode. This ensures we get the
        # git check *after* the xcode check.
        super().verify_tools()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External service APIs.
        # These are abstracted to enable testing without patching.
        self.dmgbuild = dmgbuild

    def verify_app(self, app):
        super().verify_app(app)

        if app.console_app:
            if app.packaging_format is None:
                app.packaging_format = "pkg"
            elif app.packaging_format != "pkg":
                raise BriefcaseCommandError(
                    "macOS console apps must be distributed in PKG format."
                )
        elif app.packaging_format is None:
            app.packaging_format = "dmg"

    def notarize(self, filename, identity: SigningIdentity):
        """Notarize a file.

        Submits the file to Apple for notarization; if successful, staples the
        notarization result onto the file.

        If the file is a .app, it will be archived as a .zip for submission purposes.

        :param filename: The file to notarize.
        :param identity: The code signing identity to use
        """
        try:
            if filename.suffix == ".app":
                # Archive the app into a zip.
                with self.input.wait_bar(f"Archiving {filename.name}..."):
                    archive_filename = filename.parent / "archive.zip"
                    self.tools.shutil.make_archive(
                        archive_filename.with_suffix(""),
                        format="zip",
                        root_dir=filename.parent,
                        base_dir=filename.name,
                    )
            elif filename.suffix in {".dmg", ".pkg"}:
                archive_filename = filename
            else:
                archive_filename = filename
                raise RuntimeError(
                    f"Don't know how to notarize a file of type {filename.suffix}"
                )

            profile = f"briefcase-macOS-{identity.team_id}"
            submitted = False
            store_credentials = False
            while not submitted:
                if store_credentials:
                    if not self.input.enabled:
                        raise BriefcaseCommandError(
                            f"""
The keychain does not contain credentials for the profile {profile}.
You can store these credentials by invoking:

    $ xcrun notarytool store-credentials --team-id {identity.team_id} profile

"""
                        )

                    self.logger.warning(
                        """
The notarization process uses credentials stored on your system Keychain.
You need to do this once for each signing certificate you use.

The credentials are authenticated and stored using your Apple ID, using
an app-specific Apple ID password. To generate an app-specific Apple ID
password:

  1. Sign into https://appleid.apple.com;
  2. In the 'Sign-in and Security' section, click 'App-Specific Passwords';
  3. Click on the '+' icon. You will need to provide an identifying name
     for the password. You can pick any name that makes sense to you - the
     name is only there so you can identify passwords. 'Briefcase' would be
     one possible name.
  4. Record the password somewhere safe.
"""
                    )
                    try:
                        self.tools.subprocess.run(
                            [
                                "xcrun",
                                "notarytool",
                                "store-credentials",
                                "--team-id",
                                identity.team_id,
                                profile,
                            ],
                            check=True,
                            stream_output=False,  # Command reads from stdin.
                        )
                    except subprocess.CalledProcessError as e:
                        raise BriefcaseCommandError(
                            f"Unable to store credentials for team ID {identity.team_id}."
                        ) from e

                # Attempt the notarization
                try:
                    self.logger.info()
                    self.tools.subprocess.run(
                        [
                            "xcrun",
                            "notarytool",
                            "submit",
                            archive_filename,
                            "--keychain-profile",
                            profile,
                            "--wait",
                        ],
                        check=True,
                    )
                    submitted = True
                except subprocess.CalledProcessError as e:
                    # Error when submitting for notarization.
                    # A return code of 69 (nice) indicates an issue with the
                    # keychain profile. If store_credentials is already True,
                    # then we've already tried to store them, so call the attempt
                    # a fail
                    if e.returncode == 69 and not store_credentials:
                        store_credentials = True
                    else:
                        raise BriefcaseCommandError(
                            f"""\
Unable to submit {filename.relative_to(self.base_path)} for notarization.
To find the cause of this failure, get the submission ID by running:

    xcrun notarytool history

Then run:

    xcrun notarytool log <submission-id>

to generate a full log of the error.
"""
                        ) from e
        finally:
            # Clean up house; we don't need the archive anymore.
            if archive_filename != filename:
                self.tools.os.unlink(archive_filename)

        try:
            self.logger.info()
            self.logger.info(
                f"Stapling notarization onto {filename.relative_to(self.base_path)}..."
            )
            self.tools.subprocess.run(
                ["xcrun", "stapler", "staple", filename],
                check=True,
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                f"Unable to staple notarization onto {filename.relative_to(self.base_path)}."
            )

    def package_app(
        self,
        app: AppConfig,
        notarize_app=None,
        identity=None,
        adhoc_sign=False,
        sign_installer=True,
        installer_identity=None,
        **kwargs,
    ):
        """Package an app bundle.

        :param app: The application to package
        :param notarize_app: Should the app be notarized? Default: ``True`` if the app
            has been signed with a real identity; ``False`` if the app is unsigned, or
            an ad-hoc signing identity has been used.
        :param identity: The signing identity to use to sign the app. This can be either
            the 40-digit hex checksum, or the string name of the identity. If
            unspecified, the user will be prompted for an app signing identity. Ignored
            if ``adhoc_sign`` is ``True``.
        :param adhoc_sign: If ``True``, code will be signed with ad-hoc identity of "-",
            and the resulting app will not be re-distributable.
        :param sign_installer: Should the installer be signed? Ignored unless the
            packaging format is ``pkg``.
        :param installer_identity: The signing identity to use when signing the
            installer. Ignored unless the packaging format is ``pkg``.
        """
        self.logger.info("Signing app...", prefix=app.app_name)
        if adhoc_sign:
            identity = SigningIdentity()
        else:
            identity = self.select_identity(identity=identity)

        if identity.is_adhoc:
            if notarize_app:
                raise BriefcaseCommandError(
                    "Can't notarize an app with an ad-hoc signing identity"
                )
            self.logger.warning(
                """
*************************************************************************
** WARNING: Signing with an ad-hoc identity                            **
*************************************************************************

    This app is being signed with an ad-hoc identity. The resulting
    app will run on this computer, but will not run on anyone else's
    computer.

    To generate an app that can be distributed to others, you must
    obtain an application distribution certificate from Apple, and
    select the developer identity associated with that certificate
    when running 'briefcase package'.

*************************************************************************

"""
            )
            self.logger.info("Signing app with ad-hoc identity...")
        else:
            # If we're signing, and notarization isn't explicitly disabled,
            # notarize by default.
            if notarize_app is None:
                notarize_app = True

            self.logger.info(f"Signing app with identity {identity.name}...")

        self.sign_app(app=app, identity=identity)

        if app.packaging_format == "zip":
            self.package_zip(
                app,
                notarize_app=notarize_app,
                identity=identity,
            )

        elif app.packaging_format == "pkg":
            # If the user has indicated they want to sign the installer (the default),
            # and the signing identity for the app *isn't* the adhoc identity, select an
            # identity for signing the installer.
            if sign_installer and not identity.is_adhoc:
                installer_identity = self.select_identity(
                    identity=installer_identity,
                    app_identity=identity,
                )
            else:
                installer_identity = None

            self.package_pkg(
                app,
                notarize_app=notarize_app,
                identity=identity,
                installer_identity=installer_identity,
            )

        else:  # Default packaging format is DMG
            self.package_dmg(
                app,
                notarize_app=notarize_app,
                identity=identity,
            )

    def package_zip(
        self,
        app: AppConfig,
        notarize_app: bool,
        identity: SigningIdentity,
    ):
        """Package an .app bundle in a zip file."""
        dist_path: Path = self.distribution_path(app)

        if notarize_app:
            self.logger.info(
                f"Notarizing app using team ID {identity.team_id}...",
                prefix=app.app_name,
            )
            self.notarize(self.binary_path(app), identity=identity)

        with self.input.wait_bar(f"Archiving {dist_path.name}..."):
            self.tools.shutil.make_archive(
                dist_path.with_suffix(""),
                format="zip",
                root_dir=self.binary_path(app).parent,
                base_dir=self.binary_path(app).name,
            )

    def package_pkg(
        self,
        app: AppConfig,
        notarize_app: bool,
        identity: SigningIdentity,
        installer_identity: SigningIdentity | None,
    ):
        """Package the app as an installer."""
        dist_path: Path = self.distribution_path(app)

        self.logger.info("Building PKG...", prefix=app.app_name)

        installer_path = self.bundle_path(app) / "installer"

        with self.input.wait_bar("Installing license..."):
            license_file = self.base_path / "LICENSE"
            if license_file.is_file():
                (installer_path / "resources").mkdir(exist_ok=True)
                self.tools.shutil.copy(
                    license_file,
                    installer_path / "resources/LICENSE",
                )
            else:
                raise BriefcaseCommandError(
                    """\
Your project does not contain a LICENSE file.

Create a file named `LICENSE` in the same directory as your `pyproject.toml`
with your app's licensing terms.
"""
                )

        # pkgbuild's default behavior is to make "relocatable" installs, which means
        # that if you've ever run the app, the installer will default to updating *that*
        # version, rather than putting it in the location that the installer specifies.
        # This means if you've ever used `briefcase run`, that will be the install
        # location of the "installed" app. To work around this, you have to provide a
        # plist file - but that requires providing a "root" folder that *only* contains
        # the products you want to install. So - we need to copy the built app to a
        # "clean" packaging location.
        with self.input.wait_bar("Copying app into products folder..."):
            installed_app_path = installer_path / "root" / self.binary_path(app).name
            if installed_app_path.exists():
                self.tools.shutil.rmtree(installed_app_path)
            self.tools.shutil.copytree(self.binary_path(app), installed_app_path)

        components_plist_path = self.bundle_path(app) / "installer/components.plist"

        with self.input.wait_bar("Writing component manifest..."):
            with components_plist_path.open("wb") as components_plist:
                plistlib.dump(
                    [
                        {
                            "BundleHasStrictIdentifier": True,
                            "BundleIsRelocatable": False,
                            "BundleIsVersionChecked": True,
                            "BundleOverwriteAction": "upgrade",
                            "RootRelativeBundlePath": self.binary_path(app).name,
                        }
                    ],
                    components_plist,
                )

        # Console apps are installed in /Library/Formal Name, and include the
        # post-install scripts. Normal apps are installed in /Applications, and don't
        # include the scripts.
        if app.console_app:
            install_args = [
                "--install-location",
                f"/Library/{app.formal_name}",
                "--scripts",
                installer_path / "scripts",
            ]
        else:
            install_args = ["--install-location", "/Applications"]

        with self.input.wait_bar("Building app package..."):
            installer_packages_path = installer_path / "packages"
            if installer_packages_path.exists():
                self.tools.shutil.rmtree(installer_packages_path)
            installer_packages_path.mkdir()

            self.tools.subprocess.run(
                [
                    "pkgbuild",
                    "--root",
                    installer_path / "root",
                    "--component-plist",
                    components_plist_path,
                ]
                + install_args
                + [
                    installer_packages_path / f"{app.app_name}.pkg",
                ],
                check=True,
            )

        # Build package
        with self.input.wait_bar(f"Building {dist_path.name}..."):
            if installer_identity:
                signing_options = ["--sign", installer_identity.id]
            else:
                signing_options = []

            self.tools.subprocess.run(
                [
                    "productbuild",
                    "--distribution",
                    installer_path / "Distribution.xml",
                    "--package-path",
                    installer_path / "packages",
                    "--resources",
                    installer_path / "resources",
                ]
                + signing_options
                + [
                    dist_path,
                ],
                check=True,
            )

        if notarize_app:
            self.logger.info(
                f"Notarizing PKG with team ID {installer_identity.team_id}...",
                prefix=app.app_name,
            )
            self.notarize(dist_path, identity=installer_identity)

    def package_dmg(
        self,
        app: AppConfig,
        notarize_app: bool,
        identity: SigningIdentity,
    ):
        """Package an app as a DMG installer."""
        dist_path: Path = self.distribution_path(app)
        self.logger.info("Building DMG...", prefix=app.app_name)

        with self.input.wait_bar(f"Building {dist_path.name}..."):
            dmg_settings = {
                "files": [os.fsdecode(self.binary_path(app))],
                "symlinks": {"Applications": "/Applications"},
                "icon_locations": {
                    f"{app.formal_name}.app": (75, 75),
                    "Applications": (225, 75),
                },
                "window_rect": ((600, 600), (350, 150)),
                "icon_size": 64,
                "text_size": 12,
            }

            try:
                icon_filename = self.base_path / f"{app.installer_icon}.icns"
                if not icon_filename.exists():
                    self.logger.warning(
                        f"Can't find {app.installer_icon}.icns to use as DMG installer icon"
                    )
                    raise AttributeError()
            except AttributeError:
                # No installer icon specified. Fall back to the app icon
                if app.icon:
                    icon_filename = self.base_path / f"{app.icon}.icns"
                    if not icon_filename.exists():
                        self.logger.warning(
                            f"Can't find {app.icon}.icns to use as fallback DMG installer icon"
                        )
                        icon_filename = None
                else:
                    # No app icon specified either
                    icon_filename = None

            if icon_filename:
                dmg_settings["icon"] = os.fsdecode(icon_filename)

            try:
                image_filename = self.base_path / f"{app.installer_background}.png"
                if image_filename.exists():
                    dmg_settings["background"] = os.fsdecode(image_filename)
                else:
                    self.logger.warning(
                        f"Can't find {app.installer_background}.png to use as DMG background"
                    )
            except AttributeError:
                # No installer background image provided
                pass

            self.dmgbuild.build_dmg(
                filename=os.fsdecode(dist_path),
                volume_name=f"{app.formal_name} {app.version}",
                settings=dmg_settings,
            )

        self.sign_file(dist_path, identity=identity)

        if notarize_app:
            self.logger.info(
                f"Notarizing DMG with team ID {identity.team_id}...",
                prefix=app.app_name,
            )
            self.notarize(dist_path, identity=identity)
