from __future__ import annotations

import concurrent.futures
import itertools
import os
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


class macOSMixin:
    platform = "macOS"
    supported_host_os = {"Darwin"}
    supported_host_os_reason = "macOS applications can only be built on macOS."


class macOSInstallMixin(AppPackagesMergeMixin):
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
        sender = os.fsdecode(
            self.binary_path(app) / "Contents" / "MacOS" / app.formal_name
        )
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
            kwargs = self._prepare_app_env(app=app, test_mode=test_mode)

            # Start the app in a way that lets us stream the logs
            self.tools.subprocess.run(
                [
                    "open",
                    "-n",  # Force a new app to be launched
                    os.fsdecode(self.binary_path(app)),
                ]
                + ((["--args"] + passthrough) if passthrough else []),
                cwd=self.tools.home_path,
                check=True,
                **kwargs,
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

    def entitlements_path(self, app: AppConfig):
        return self.bundle_path(app) / self.path_index(app, "entitlements_path")

    def select_identity(self, identity=None):
        """Get the codesigning identity to use.

        :param identity: A pre-specified identity (either the 40-digit hex checksum, or
            the string name of the identity). If provided, it will be validated against
            the list of available identities to confirm that it is a valid codesigning
            identity.
        :returns: The final identity to use
        """
        # Obtain the valid codesigning identities.
        identities = self.get_identities(self.tools, "codesigning")
        identities["-"] = ADHOC_IDENTITY_NAME

        if identity:
            try:
                # Try to look up the identity as a hex checksum
                identity_name = identities[identity]
                return identity, identity_name
            except KeyError as e:
                # Try to look up the identity as readable name
                try:
                    reverse_lookup = {name: ident for ident, name in identities.items()}
                    identity_id = reverse_lookup[identity]
                    return identity_id, identity
                except KeyError:
                    # Not found as an ID or name
                    raise BriefcaseCommandError(
                        f"Invalid code signing identity {identity}"
                    ) from e

        self.input.prompt()
        self.input.prompt("Select code signing identity to use:")
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

    $ briefcase {self.command} macOS -i {identity}

or

    $ briefcase {self.command} macOS -i "{identity_name}"
"""
            )

        return identity, identity_name

    def sign_file(self, path, identity, entitlements=None):
        """Code sign a file.

        :param path: The path to the file to sign.
        :param identity: The code signing identity to use. Either the 40-digit hex
            checksum, or the string name of the identity.
        :param entitlements: The path to the entitlements file to use.
        """
        options = "runtime" if identity != "-" else None
        process_command = [
            "codesign",
            os.fsdecode(path),
            "--sign",
            identity,
            "--force",
        ]
        if entitlements:
            process_command.append("--entitlements")
            process_command.append(os.fsdecode(entitlements))
        if options:
            process_command.append("--options")
            process_command.append(options)

        if self.logger.verbosity >= 1:
            self.logger.info(f"Signing {Path(path).relative_to(self.base_path)}")

        try:
            self.tools.subprocess.run(
                process_command,
                stderr=subprocess.PIPE,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            errors = e.stderr
            if "code object is not signed at all" in errors:
                if self.logger.verbosity >= 1:
                    self.logger.info(
                        f"... {Path(path).relative_to(self.base_path)} requires a deep sign; retrying"
                    )
                try:
                    self.tools.subprocess.run(
                        process_command + ["--deep"],
                        stderr=subprocess.PIPE,
                        check=True,
                    )
                except subprocess.CalledProcessError as e:
                    raise BriefcaseCommandError(
                        f"Unable to deep code sign {path}."
                    ) from e

            elif any(
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
                if self.logger.verbosity >= 1:
                    self.logger.info(
                        f"... {Path(path).relative_to(self.base_path)} does not require a signature"
                    )
                return
            else:
                raise BriefcaseCommandError(f"Unable to code sign {path}.")

    def sign_app(self, app, identity):
        """Sign an entire app with a specific identity.

        :param app: The app to sign
        :param identity: The signing identity to use
        """
        bundle_path = self.binary_path(app)
        resources_path = bundle_path / "Contents" / "Resources"
        frameworks_path = bundle_path / "Contents" / "Frameworks"

        sign_targets = []

        for folder in (resources_path, frameworks_path):
            # Sign all Mach-O executable objects
            sign_targets.extend(
                path
                for path in folder.rglob("*")
                if not path.is_dir() and is_mach_o_binary(path)
            )

            # Sign all embedded frameworks
            sign_targets.extend(folder.rglob("*.framework"))

            # Sign all embedded app objects
            sign_targets.extend(folder.rglob("*.app"))

        # Sign the bundle path itself
        sign_targets.append(bundle_path)

        # Run signing through a ThreadPoolExecutor so that they run in parallel.
        # However, we need to ensure that objects are signed from the inside out
        # (i.e., a folder must be signed *after* all it's contents has been
        # signed). To do this, we sort the list of signing targets in reverse
        # lexicographic order, and then group all the signing targets by parent.
        # This sorts all the signable files into folders; and sign all files in
        # a folder before sorting the next group. This ensures that longer paths
        # are signed first, and all files in a folder are signed before the
        # folder is signed.
        #
        # NOTE: We are relying on the fact that the final iteration order
        # produced by groupby() reflects the order in which groups are found in
        # the input data. The documentation for groupby() says that a new break
        # is created every time a new group is found in the input data; sorting
        # the input in reverse order ensures that only one group is found per folder,
        # and that the deepest folder is found first.
        progress_bar = self.input.progress_bar()
        task_id = progress_bar.add_task("Signing App", total=len(sign_targets))
        with progress_bar:
            for _, names in itertools.groupby(
                sorted(sign_targets, reverse=True),
                lambda name: name.parent,
            ):
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    for path in names:
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
        "The app will only run on this machine; it cannot be redistributed to others."
    )
    IDENTITY_HELP = (
        "The code signing identity to use; either the 40-digit hex "
        "checksum, or the full name of the identity."
    )

    @property
    def packaging_formats(self):
        return ["app", "dmg"]

    @property
    def default_packaging_format(self):
        return "dmg"

    def distribution_path(self, app):
        if app.packaging_format == "dmg":
            return self.dist_path / f"{app.formal_name}-{app.version}.dmg"
        else:
            return self.dist_path / f"{app.formal_name}-{app.version}.app.zip"

    def add_options(self, parser):
        super().add_options(parser)
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

    def team_id_from_identity(self, identity_name):
        """Extract the team ID from the full identity name.

        The identity name will be in the form:
            Some long identifying name (Team ID)

        :param identity_name: The full identity name
        :returns: The team ID string.
        """
        try:
            return re.match(r".*\(([\dA-Z]*)\)", identity_name)[1]
        except TypeError:
            raise BriefcaseCommandError(
                f"Couldn't extract Team ID from signing identity {identity_name!r}"
            )

    def notarize(self, filename, team_id):
        """Notarize a file.

        Submits the file to Apple for notarization; if successful, staples the
        notarization result onto the file.

        If the file is a .app, it will be archived as a .zip for submission purposes.

        :param filename: The file to notarize.
        :param team_id: The team ID to
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
            elif filename.suffix == ".dmg":
                archive_filename = filename
            else:
                archive_filename = filename
                raise RuntimeError(
                    f"Don't know how to notarize a file of type {filename.suffix}"
                )

            profile = f"briefcase-macOS-{team_id}"
            submitted = False
            store_credentials = False
            while not submitted:
                if store_credentials:
                    if not self.input.enabled:
                        raise BriefcaseCommandError(
                            f"""
The keychain does not contain credentials for the profile {profile}.
You can store these credentials by invoking:

    $ xcrun notarytool store-credentials --team-id {team_id} profile
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
                                team_id,
                                profile,
                            ],
                            check=True,
                            stream_output=False,  # Command reads from stdin.
                        )
                    except subprocess.CalledProcessError as e:
                        raise BriefcaseCommandError(
                            f"Unable to store credentials for team ID {team_id}."
                        ) from e

                # Attempt the notarization
                try:
                    self.logger.info()
                    self.tools.subprocess.run(
                        [
                            "xcrun",
                            "notarytool",
                            "submit",
                            os.fsdecode(archive_filename),
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
                            f"Unable to submit {filename.relative_to(self.base_path)} for notarization."
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
                [
                    "xcrun",
                    "stapler",
                    "staple",
                    os.fsdecode(filename),
                ],
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
        **kwargs,
    ):
        """Package an app bundle.

        :param app: The application to package
        :param notarize_app: Should the app be notarized? Default: ``True`` if the
            app has been signed with a real identity; ``False`` if the app is
            unsigned, or an ad-hoc signing identity has been used.
        :param identity: The code signing identity to use. This can be either
            the 40-digit hex checksum, or the string name of the identity.
            If unspecified, the user will be prompted for a code signing
            identity. Ignored if ``adhoc_sign`` is ``True``.
        :param adhoc_sign: If ``True``, code will be signed with ad-hoc identity
            of "-", and the resulting app will not be re-distributable.
        """
        if adhoc_sign:
            identity = "-"
            identity_name = ADHOC_IDENTITY_NAME
        else:
            identity, identity_name = self.select_identity(identity=identity)

        if identity == "-":
            if notarize_app:
                raise BriefcaseCommandError(
                    "Can't notarize an app with an ad-hoc signing identity"
                )
            self.logger.info(
                "Signing app with ad-hoc identity...",
                prefix=app.app_name,
            )
            self.logger.warning(
                (
                    "Because you are signing with the ad-hoc identity, this "
                    "app will run, but cannot be re-distributed."
                ),
                prefix=app.app_name,
            )
        else:
            # If we're signing, and notarization isn't explicitly disabled,
            # notarize by default.
            if notarize_app is None:
                notarize_app = True

            self.logger.info(
                f"Signing app with identity {identity_name}...", prefix=app.app_name
            )

            if notarize_app:
                team_id = self.team_id_from_identity(identity_name)

        self.sign_app(app=app, identity=identity)

        if app.packaging_format == "app":
            if notarize_app:
                self.logger.info(
                    f"Notarizing app using team ID {team_id}...",
                    prefix=app.app_name,
                )
                self.notarize(self.binary_path(app), team_id=team_id)

            with self.input.wait_bar(
                f"Archiving {self.distribution_path(app).name}..."
            ):
                self.tools.shutil.make_archive(
                    self.distribution_path(app).with_suffix(""),
                    format="zip",
                    root_dir=self.binary_path(app).parent,
                    base_dir=self.binary_path(app).name,
                )

        else:  # Default packaging format is DMG
            self.logger.info("Building DMG...", prefix=app.app_name)

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

            dmg_path = self.distribution_path(app)
            self.dmgbuild.build_dmg(
                filename=os.fsdecode(dmg_path),
                volume_name=f"{app.formal_name} {app.version}",
                settings=dmg_settings,
            )

            self.sign_file(
                dmg_path,
                identity=identity,
            )

            if notarize_app:
                self.logger.info(
                    f"Notarizing DMG with team ID {team_id}...",
                    prefix=app.app_name,
                )
                self.notarize(dmg_path, team_id=team_id)
