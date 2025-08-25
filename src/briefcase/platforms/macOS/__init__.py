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

from packaging.version import Version

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError, NotarizationInterrupted
from briefcase.integrations.subprocess import (
    get_process_id_by_command,
    is_process_dead,
    json_parser,
)
from briefcase.integrations.xcode import XcodeCliTools, get_identities
from briefcase.platforms.macOS.filters import macOS_log_clean_filter
from briefcase.platforms.macOS.utils import AppPackagesMergeMixin, is_mach_o_binary

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
            self.profile = None
        else:
            self.name = name
            self.team_id = self.team_id_from_name(name)
            self.profile = f"briefcase-macOS-{self.team_id}"

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
    platform_target_version: str | None = "0.3.20"

    def bundle_package_path(self, app) -> Path:
        return self.binary_path(app)

    def is_icloud_synced(self, path: Path) -> bool:
        """Determine if a path is on an iCloud drive.

        This is done by looking for the "com.apple.fileprovider.fpfs#P" resource fork.
        This fork only appears on *some* directories - most notably, `.app` folders.

        :param path: The location to check.
        :returns: True if the location has iCloud resource markers.
        """
        # Check if the path is on an iCloud mounted drive.
        try:
            # Check for the iCloud resource fork. "Good" operation produces an error,
            # so use quiet mode.
            self.tools.subprocess.check_output(
                [
                    "xattr",
                    "-p",
                    "com.apple.fileprovider.fpfs#P",
                    path,
                ],
                quiet=1,
            )
            # The resource fork was found.
            return True
        except subprocess.CalledProcessError:
            # The resource fork was not found.
            # This includes the file not existing.
            return False

    def verify_not_on_icloud(self, app: AppConfig, cleanup=False):
        """Confirm that the app is *not* on an iCloud synchronized drive.

        When a `.app` folder is on an iCloud-synchronized drive, iCloud adds filesystem
        metadata to the folder. This metadata can't be removed (iCloud will just put it
        back again), but it also conflicts with app signing. So - if we detect this
        metadata, the project has been generated somewhere that ultimately won't work.

        Optionally, this method will clean up the bundle if the verification fails.

        :param app: The app to check.
        :param cleanup: Should the app bundle be deleted if verification fails?
        """
        if self.is_icloud_synced(self.binary_path(app)):
            msg = [
                """\
Your project is in a folder that is synchronized with iCloud. This interferes
with the operation of macOS code signing."""
            ]
            if cleanup:
                self.tools.shutil.rmtree(self.bundle_path(app))
                msg.append(
                    f"""
Move your project to a location that is not synchronized with iCloud,
and re-run `briefcase {self.command}`."""
                )
            else:
                bundle_path = self.bundle_path(app).relative_to(self.base_path)
                msg.append(
                    f"""
Delete the {bundle_path} folder, move your project to location
that is not synchronized with iCloud, and re-run `briefcase {self.command}`."""
                )
            raise BriefcaseCommandError("\n".join(msg))


class macOSCreateMixin(AppPackagesMergeMixin):
    hidden_app_properties = {"permission", "entitlement"}

    def generate_app_template(self, app: AppConfig):
        """Create an application bundle.

        :param app: The config object for the app
        """
        # Before we generate the app template, make sure the package path and formal
        # name match. This will always be the case for internal apps; they might not be
        # aligned for external apps. We can't do this in verify, because app
        # verification occurs after the template is generated.
        if self.package_path(app).name != f"{app.formal_name}.app":
            raise BriefcaseCommandError(
                "The app bundle referenced by external_package_path "
                f"({self.package_path(app).name})\n"
                f"does not match the formal name of the app ({app.formal_name!r}).\n"
            )

        super().generate_app_template(app=app)
        # If we discover we're on iCloud during app creation, we can clean up the app
        # folder. This *may* return a false negative (i.e., not accurately detect that
        # we *are* on iCloud, because it takes a moment for the iCloud daemon to detect
        # that a new folder has been created; however, if this occurs, it will be
        # picked up on the next run of any Briefcase command).
        self.verify_not_on_icloud(app, cleanup=True)

    def _install_app_requirements(
        self,
        app: AppConfig,
        requires: list[str],
        app_packages_path: Path,
        **kwargs,
    ):
        try:
            # Determine the min macOS version from the framework metadata
            # of the macos-arm64_x86_64 slice of the XCframework
            plist_file = (
                self.support_path(app)
                / "Python.xcframework/macos-arm64_x86_64"
                / "Python.framework/Resources/Info.plist"
            )
            with plist_file.open("rb") as f:
                info_plist = plistlib.load(f)

            support_min_version = info_plist.get("MinimumOSVersion", "11.0")
        except FileNotFoundError:
            # If a plist file couldn't be found, it's an old-style support package;
            # Determine the min macOS version from the VERSIONS file in the support package.
            versions = dict(
                [part.strip() for part in line.split(": ", 1)]
                for line in (
                    (self.support_path(app) / "VERSIONS")
                    .read_text(encoding="UTF-8")
                    .split("\n")
                )
                if ": " in line
            )
            support_min_version = versions.get("Min macOS version", "11.0")

        # Check that the app's definition is compatible with the support package
        # If the app doesn't specify a minimum version, use the support package
        # minimum version as a default.
        macOS_min_version = getattr(app, "min_os_version", support_min_version)

        if Version(macOS_min_version) < Version(support_min_version):
            raise BriefcaseCommandError(
                f"Your macOS app specifies a minimum macOS version of {macOS_min_version}, "
                f"but the support package only supports {support_min_version}"
            )

        macOS_min_tag = macOS_min_version.replace(".", "_")

        if getattr(app, "universal_build", True):
            # Perform the initial install targeting the current platform
            host_app_packages_path = (
                self.bundle_path(app) / f"app_packages.{self.tools.host_arch}"
            )
            # A standard install, except we explicitly reject installs from source
            # tarballs with `--only-binary :all:`. This is for two reasons:
            #
            # 1. Consistency. We need to use `--only-binary :all:` when we do the second
            #    "other arch" wheel install because of use of the `--platform` argument;
            #    if we only reject source tarballs from one of the installs, then a
            #    package that only provides binary wheels for one architecture would
            #    cause inconsistent results depending on which platform was the host;
            #    and
            #
            # 2. Security. Installs from source tarball involve executing arbitrary code
            #    at time of installation; and it makes the entire development
            #    environment building the app a vector for introducing vulnerabilities
            #    into an app. Forcing the use of binary wheels ensures that we can know
            #    with certainty the provenance of any binary content in the app.
            #
            # Since Briefcase is a tool designed to produce redistributable binaries,
            # we've made the judgement call that the (minor, with known workarounds)
            # inconvenience of not being able to use source tarballs is outweighed by
            # the need to produce reliable, repeatable binary artefacts.
            super()._install_app_requirements(
                app,
                requires=requires,
                app_packages_path=host_app_packages_path,
                pip_args=[
                    "--only-binary",
                    ":all:",
                    "--platform",
                    f"macosx_{macOS_min_tag}_{self.tools.host_arch}",
                ],
                install_hint=f"""

This may be because an {self.tools.host_arch} wheel that is compatible with a minimum
macOS version of {macOS_min_version} is not available.
""",
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
                with self.console.wait_bar(
                    f"Installing binary app requirements for {other_arch}..."
                ):
                    self._pip_install(
                        app,
                        app_packages_path=other_app_packages_path,
                        pip_args=[
                            "--no-deps",
                            "--platform",
                            f"macosx_{macOS_min_tag}_{other_arch}",
                            "--only-binary",
                            ":all:",
                        ]
                        + [
                            f"{package}=={version}"
                            for package, version in binary_packages
                        ],
                        install_hint=f"""

This may be because an {other_arch} wheel that is compatible with a minimum
macOS version of {macOS_min_version} is not available.

You may need to build a non-universal app by setting:

    universal_build = False

in the macOS configuration section of your pyproject.toml.
""",
                    )
            else:
                self.console.info("All packages are pure Python, or universal.")

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
                pip_args=[
                    "--only-binary",
                    ":all:",
                    "--platform",
                    f"macosx_{macOS_min_tag}_{self.tools.host_arch}",
                ],
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
        passthrough: list[str],
        **kwargs,
    ):
        """Start the application.

        :param app: The config object for the app
        :param passthrough: The list of arguments to pass to the app
        """
        # Console apps must operate in non-streaming mode so that console input can
        # be handled correctly. However, if we're in test mode, we *must* stream so
        # that we can see the test exit sentinel.
        if app.console_app:
            self.run_console_app(
                app,
                passthrough=passthrough,
                **kwargs,
            )
        else:
            self.run_gui_app(
                app,
                passthrough=passthrough,
                **kwargs,
            )

    def run_console_app(
        self,
        app: AppConfig,
        passthrough: list[str],
        **kwargs,
    ):
        """Start the console application.

        :param app: The config object for the app
        :param passthrough: The list of arguments to pass to the app
        """
        sub_kwargs = self._prepare_app_kwargs(app=app)
        cmdline = [self.binary_path(app) / f"Contents/MacOS/{app.formal_name}"]
        cmdline.extend(passthrough)

        if app.test_mode:
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
            self._stream_app_logs(app, popen=app_popen)

        else:
            try:
                # Start the app directly
                self.console.info("=" * 75)
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
        passthrough: list[str],
        **kwargs,
    ):
        """Start the GUI application.

        :param app: The config object for the app
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
            sub_kwargs = self._prepare_app_kwargs(app=app)

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
                console=self.console,
            )

            if app_pid is None:
                raise BriefcaseCommandError(
                    f"Unable to find process for app {app.app_name} to start log streaming."
                )

            # Stream the app logs.
            self._stream_app_logs(
                app,
                popen=log_popen,
                clean_filter=macOS_log_clean_filter,
                clean_output=True,
                stop_func=lambda: is_process_dead(app_pid),
                log_stream=True,
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(f"Unable to start app {app.app_name}.")
        finally:
            # Ensure the App also terminates when exiting. The ordering here is a little
            # odd; the if could/should be outside the context manager, but coverage has
            # issues with that arrangement on some Python versions (3.10, 3.14)
            with suppress(ProcessLookupError):
                if app_pid:
                    self.tools.os.kill(app_pid, SIGTERM)


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
        allow_adhoc: bool = True,
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
        :param allow_adhoc: Should the adhoc identities be allowed?
        :returns: The final identity to use
        """
        # If the adhoc identity is allowed, add it first so it appears first in the list
        # of options.
        identities = {}
        if allow_adhoc:
            identities["-"] = ADHOC_IDENTITY_NAME

        # Obtain the valid codesigning identities. These are the identities that could
        # be used for app signing.
        identities.update(self.get_identities(self.tools, "codesigning"))

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

        identity = self.console.selection_question(
            intro=f"Select {ident_type} signing identity to use:",
            description=f"{ident_type.title()} Signing Identity",
            options=identities,
        )
        identity_name = identities[identity]
        if identity == "-":
            self.console.info(
                f"""
In future, you could specify this signing identity by using:

    $ briefcase {self.command} macOS {self.output_format} --adhoc-sign ...

"""
            )
        else:
            self.console.info(
                f"""
In future, you could specify this signing identity by using:

    $ briefcase {self.command} macOS {self.output_format} {ident_option} {identity} ...

or

    $ briefcase {self.command} macOS {self.output_format} {ident_option} "{identity_name}" ...

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

        self.console.verbose(f"Signing {Path(path).relative_to(self.base_path)}")

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
                self.console.verbose(
                    f"... {Path(path).relative_to(self.base_path)} does not require a signature"
                )
                return
            else:
                self.tools.subprocess.output_error(e)
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
        bundle_path = self.package_path(app)
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
        progress_bar = self.console.progress_bar()
        task_id = progress_bar.add_task("Signing App", total=len(sign_targets))
        with progress_bar:
            for group in self.tools.file.sorted_depth_first_groups(sign_targets):
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=1 if self.console.is_deep_debug else None
                ) as executor:
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

    def notarization_path(self, app: AppConfig) -> Path:
        """The file that is submitted for notarization."""
        if app.packaging_format == "zip":
            # Notarization for bare .app's is applied to the binary, not the
            # distribution artefact, with the distribution artefact being
            # created after notarization has completed.
            return self.package_path(app)
        else:
            return self.distribution_path(app)

    def distribution_path(self, app: AppConfig) -> Path:
        """The path to the final distribution artefact."""
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
        parser.add_argument(
            "--resume",
            dest="submission_id",
            help="The notarization submission ID to resume",
            required=False,
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

    def clean_dist_folder(self, app, **options):
        """Clean up any existing artefacts in the dist folder.

        If we are resuming a notarization session verify that the artefact exists, but
        *do not* delete it.

        :param app: The app being packaged.
        :param submission_id: The notarization submission being resumed.
        :param options: Any additional arguments passed to the package command.
        """
        if options.get("submission_id"):
            if not self.notarization_path(app).exists():
                raise BriefcaseCommandError(
                    "Notarization cannot be resumed, as the notarization artefact "
                    "associated with this app "
                    f"({self.notarization_path(app).relative_to(self.base_path)}) "
                    "does not exist."
                )

            # If the packaging format is zip, the distribution artefact is created
            # *after* completion of notarization. If there's an existing distribution
            # artefact, it must be from a previous notarization/stapling attempt.
            if app.packaging_format == "zip":
                super().clean_dist_folder(app, **options)
        else:
            super().clean_dist_folder(app, **options)

    def ditto_archive(
        self,
        app_filename: Path,
        archive_filename: Path,
    ):  # pragma: no-cover-if-not-macos
        """Create an archive of an app using ditto.

        Although the archive format is ".zip", we can't use standard Zip tools, as they
        don't preserve UTF-8 encoding on all resources. Instead, we need to use `ditto`,
        which is provided as part of macOS developer tooling. See
        https://forums.developer.apple.com/forums/thread/116831 and
        https://developer.apple.com/library/archive/technotes/tn2206/_index.html for
        more details.

        :param app_filename: The filename of the app to archive
        :param archive_filename: The filename of the archive to produce
        """
        try:
            self.tools.subprocess.run(
                [
                    "/usr/bin/ditto",
                    "-c",
                    "-k",
                    "--sequesterRsrc",
                    "--keepParent",
                    app_filename,
                    archive_filename,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to archive {app_filename.name}") from e

    def notarize(
        self,
        app: AppConfig,
        identity: SigningIdentity,
        installer_identity: SigningIdentity | None = None,
    ):
        """Submit a file for notarization, and wait for that notarization to be
        completed.

        :param app: The app to notarize.
        :param identity: The code signing used to notarize the app.
        :param installer_identity: The signing identity to use when signing the
            installer. Optional unless the packaging format is ``pkg``.
        """
        # Determine the arguments that would be needed to reproduce this notarization
        if installer_identity:
            identity_args = (
                f"--identity {identity.id} --installer-identity {installer_identity.id}"
            )
            notarization_identity = installer_identity
        else:
            identity_args = f"--identity {identity.id}"
            notarization_identity = identity

        format_args = f"-p {app.packaging_format}"

        # Submit the app for notarization
        submission_id = self.submit_notarization(app, identity=notarization_identity)

        self.console.warning(
            f"""
Briefcase will now wait for Apple to approve the notarization request.
This can take some time - in some cases, hours.

If notarization is interrupted, you can resume by running:

    briefcase package macOS {self.output_format} {format_args} {identity_args} --resume {submission_id}

"""
        )

        self.finalize_notarization(
            app,
            identity=notarization_identity,
            submission_id=submission_id,
        )

    def submit_notarization(self, app, identity: SigningIdentity) -> str:
        """Submit a file for notarization, returning the ID of the notarizatzion task.

        If the file is a .app, it will be archived as a .zip for submission purposes.

        :param app: The app to notarize.
        :param identity: The code signing identity to use.
        :returns: The ID of the notarization task.
        """
        filename = self.notarization_path(app)
        try:
            if app.packaging_format == "zip":
                self.console.info()
                with self.console.wait_bar(
                    f"Archiving {filename.name} for notarization..."
                ):
                    archive_filename = filename.parent / (filename.name + ".zip")
                    self.ditto_archive(filename, archive_filename)
            else:
                archive_filename = filename

            submission_id = None
            store_credentials = False
            while not submission_id:
                if store_credentials:
                    if not self.console.input_enabled:
                        raise BriefcaseCommandError(
                            f"""
The keychain does not contain credentials for the profile {identity.profile}.
You can store these credentials by invoking:

    $ xcrun notarytool store-credentials --team-id {identity.team_id} {identity.profile}

"""
                        )

                    self.console.warning(
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
                                identity.profile,
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
                    self.console.info()
                    with self.console.wait_bar("Submitting app for notarization..."):
                        submission = self.tools.subprocess.parse_output(
                            json_parser,
                            [
                                "xcrun",
                                "notarytool",
                                "submit",
                                archive_filename,
                                "--keychain-profile",
                                identity.profile,
                                "--output-format",
                                "json",
                            ],
                            quiet=1,
                        )
                        submission_id = submission["id"]
                except subprocess.CalledProcessError as e:
                    # Error when submitting for notarization.
                    # A return code of 69 (nice) indicates an issue with the
                    # keychain profile. If store_credentials is already True,
                    # then we've already tried to store them, so call the attempt
                    # a fail
                    if e.returncode == 69 and not store_credentials:
                        store_credentials = True
                    else:
                        self.tools.subprocess.output_error(e)
                        raise BriefcaseCommandError(
                            f"Unable to submit {filename.relative_to(self.base_path)} for notarization."
                        ) from e
        finally:
            # If we're using .zip packaging, the archive is temporary and isn't used for
            # distribution, so we can clean up.
            if archive_filename != filename:
                self.tools.os.unlink(archive_filename)

        return submission_id

    def validate_submission_id(
        self,
        app: AppConfig,
        identity: SigningIdentity,
        submission_id: str,
    ):
        with self.console.wait_bar("Determining validity of submission ID..."):
            try:
                response = self.tools.subprocess.parse_output(
                    json_parser,
                    [
                        "xcrun",
                        "notarytool",
                        "history",
                        "--keychain-profile",
                        identity.profile,
                        "--output-format",
                        "json",
                    ],
                )

                id_matches = [
                    submission
                    for submission in response["history"]
                    if submission["id"] == submission_id
                ]

                expected_filename = id_matches[0]["name"]
                # .app files are zipped for notarization, but the app itself is
                # notarized; strip the .zip suffix for filename matching purposes.
                if expected_filename.endswith(".zip"):
                    expected_filename = expected_filename[:-4]

                if expected_filename != self.notarization_path(app).name:
                    raise BriefcaseCommandError(
                        f"{submission_id} is not a submission ID for this project. "
                        f"It notarizes a file named {expected_filename}"
                    )
            except IndexError:
                raise BriefcaseCommandError(
                    f"{submission_id} is not a known submission ID for this identity."
                )
            except subprocess.CalledProcessError:
                raise BriefcaseCommandError(
                    "Unable to invoke notarytool to determine validity of submission ID.\n"
                    "Are you sure this is the identity that was used to notarize the app?"
                )

    def finalize_notarization(
        self,
        app: AppConfig,
        identity: SigningIdentity,
        submission_id: str,
    ):
        """Finalize a notarization task.

        Polls to check the current notarization status; once notarization approval is
        received, the notarization is stapled onto the distribution artefact.

        :param app: The app to notarize.
        :param identity: The code signing identity to use.
        :param submission_id: The submission ID of the notarization task to finalize.
        """
        try:
            with self.console.wait_bar("Waiting for notarization acceptance..."):
                accepted = False
                while not accepted:
                    try:
                        response = self.tools.subprocess.parse_output(
                            json_parser,
                            [
                                "xcrun",
                                "notarytool",
                                "log",
                                "--keychain-profile",
                                identity.profile,
                                submission_id,
                            ],
                            quiet=1,
                        )

                        if response["status"] == "Accepted":
                            accepted = True
                        elif response["status"] == "Invalid":
                            summary = response.get(
                                "statusSummary", "No details provided"
                            )
                            raise BriefcaseCommandError(
                                f"Notarization was rejected: {summary}\n"
                                + "\n".join(
                                    f"""
    * ({issue.get("severity", "?")}) {issue.get("path")} [{issue.get("architecture", "unknown architecture")}]
      {issue.get("message")}
      {issue.get("docUrl", "(No additional help available)")}"""
                                    for issue in response.get("issues", [])
                                )
                            )
                        else:
                            raise BriefcaseCommandError(
                                f"Unexpected notarization status: {response['status']}"
                            )
                    except subprocess.CalledProcessError as e:
                        if e.returncode == 69:
                            # Error code 69 (nice) indicates the server can't give a log
                            # response for the provided submission ID. We've already
                            # validated that it's a valid submission ID, so that means
                            # notarization isn't complete yet. Try again in 10 seconds.
                            time.sleep(10)
                        else:
                            self.tools.subprocess.output_error(e)
                            raise BriefcaseCommandError(
                                "Unknown problem retrieving notarization status."
                            ) from e

        except KeyboardInterrupt:
            raise NotarizationInterrupted("Notarization interrupted by user.")
        else:
            filename = self.notarization_path(app)
            try:
                self.console.info()
                self.console.info(
                    f"Stapling notarization onto {filename.relative_to(self.base_path)}..."
                )
                self.tools.subprocess.run(
                    ["xcrun", "stapler", "staple", filename],
                    check=True,
                )
            except subprocess.CalledProcessError:
                raise BriefcaseCommandError(
                    f"Unable to staple notarization onto {filename.relative_to(self.base_path)}"
                )

        # Notarization on a zip package is performed on the bare app, so we can't
        # complete packaging until notarization has completed.
        if app.packaging_format == "zip":
            self.finalize_package_zip(app)

    def package_app(
        self,
        app: AppConfig,
        notarize_app=None,
        identity=None,
        adhoc_sign=False,
        sign_installer=True,
        installer_identity=None,
        submission_id=None,
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
        :param submission_id: The submission ID of the notarization task to resume.
        """
        # Confirm the project isn't currently on an iCloud synced drive.
        self.verify_not_on_icloud(app)

        if submission_id:
            # If we're resuming notarization, we *can't* use an adhoc identity,
            # so don't allow it to be selected.
            identity = self.select_identity(identity=identity, allow_adhoc=False)

            if app.packaging_format == "pkg":
                notarization_identity = self.select_identity(
                    identity=installer_identity,
                    app_identity=identity,
                )
            else:
                notarization_identity = identity

            self.console.info(
                f"Resuming notarization for submission {submission_id}",
                prefix=app.app_name,
            )

            self.console.info()
            self.validate_submission_id(
                app,
                identity=notarization_identity,
                submission_id=submission_id,
            )

            self.console.info()
            self.finalize_notarization(
                app,
                identity=notarization_identity,
                submission_id=submission_id,
            )
            return

        # It's a normal packaging pass.
        self.console.info("Signing app...", prefix=app.app_name)
        if adhoc_sign:
            identity = SigningIdentity()
        else:
            identity = self.select_identity(identity=identity)

        if identity.is_adhoc:
            if notarize_app:
                raise BriefcaseCommandError(
                    "Can't notarize an app with an ad-hoc signing identity"
                )
            self.console.warning(
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
            self.console.info("Signing app with ad-hoc identity...")
        else:
            # If we're signing, and notarization isn't explicitly disabled,
            # notarize by default.
            if notarize_app is None:
                notarize_app = True

            self.console.info(f"Signing app with identity {identity.name}...")

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
        """Package an .app bundle in a zip file.

        If we're notarizing, this doesn't actually create the distribution artefact.
        Notarization on a zip package is performed on the bare app, so we can't complete
        packaging until notarization has completed. We call ``finalize_package_zip()``
        as part of completing zip notarization.
        """
        if notarize_app:
            self.console.info(
                f"Notarizing app using team ID {identity.team_id}...",
                prefix=app.app_name,
            )
            self.notarize(app, identity=identity)
        else:
            self.finalize_package_zip(app)

    def finalize_package_zip(self, app: AppConfig):
        """Finalize the zip packaging process."""
        # Build the final archive for distribution
        with self.console.wait_bar(
            f"Building final distribution archive for {self.package_path(app).name}..."
        ):
            self.ditto_archive(self.package_path(app), self.distribution_path(app))

    def package_pkg(
        self,
        app: AppConfig,
        notarize_app: bool,
        identity: SigningIdentity,
        installer_identity: SigningIdentity | None,
    ):
        """Package the app as an installer."""
        dist_path: Path = self.distribution_path(app)

        self.console.info("Building PKG...", prefix=app.app_name)

        installer_path = self.bundle_path(app) / "installer"

        with self.console.wait_bar("Installing license..."):
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
        with self.console.wait_bar("Copying app into products folder..."):
            installed_app_path = installer_path / "root" / self.package_path(app).name
            if installed_app_path.exists():
                self.tools.shutil.rmtree(installed_app_path)
            self.tools.shutil.copytree(
                self.package_path(app),
                installed_app_path,
                # Ensure that symlinks are preserved in the duplication.
                symlinks=True,
            )

        components_plist_path = self.bundle_path(app) / "installer/components.plist"

        with self.console.wait_bar("Writing component manifest..."):
            with components_plist_path.open("wb") as components_plist:
                plistlib.dump(
                    [
                        {
                            "BundleHasStrictIdentifier": True,
                            "BundleIsRelocatable": False,
                            "BundleIsVersionChecked": True,
                            "BundleOverwriteAction": "upgrade",
                            "RootRelativeBundlePath": self.package_path(app).name,
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

        with self.console.wait_bar("Building app package..."):
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
        with self.console.wait_bar(f"Building {dist_path.name}..."):
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
            self.console.info(
                f"Notarizing PKG with team ID {installer_identity.team_id}...",
                prefix=app.app_name,
            )
            self.notarize(
                app,
                identity=identity,
                installer_identity=installer_identity,
            )

    def package_dmg(
        self,
        app: AppConfig,
        notarize_app: bool,
        identity: SigningIdentity,
    ):
        """Package an app as a DMG installer."""
        dist_path: Path = self.distribution_path(app)
        self.console.info("Building DMG...", prefix=app.app_name)

        with self.console.wait_bar(f"Building {dist_path.name}..."):
            dmg_settings = {
                "files": [os.fsdecode(self.package_path(app))],
                "symlinks": {"Applications": "/Applications"},
                "icon_locations": {
                    self.package_path(app).name: (75, 75),
                    "Applications": (225, 75),
                },
                "window_rect": ((600, 600), (350, 150)),
                "icon_size": 64,
                "text_size": 12,
            }

            try:
                icon_filename = self.base_path / f"{app.installer_icon}.icns"
                if not icon_filename.exists():
                    self.console.warning(
                        f"Can't find {app.installer_icon}.icns to use as DMG installer icon"
                    )
                    raise AttributeError()
            except AttributeError:
                # No installer icon specified. Fall back to the app icon
                if app.icon:
                    icon_filename = self.base_path / f"{app.icon}.icns"
                    if not icon_filename.exists():
                        self.console.warning(
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
                    self.console.warning(
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
            self.console.info(
                f"Notarizing DMG with team ID {identity.team_id}...",
                prefix=app.app_name,
            )
            self.notarize(app, identity=identity)
