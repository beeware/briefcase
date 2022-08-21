import os
import re
import subprocess
import time
from pathlib import Path
from zipfile import ZipFile

from briefcase.config import BaseConfig
from briefcase.console import select_option
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import get_process_id_by_command, is_process_dead
from briefcase.integrations.xcode import (
    get_identities,
    verify_command_line_tools_install,
)

try:
    import dmgbuild
except ImportError:
    # On non-macOS platforms, dmgbuild won't be installed.
    # Allow the plugin to be loaded; raise an error when tools are verified.
    dmgbuild = None


DEFAULT_OUTPUT_FORMAT = "app"


class macOSMixin:
    platform = "macOS"


class macOSRunMixin:
    def run_app(self, app: BaseConfig, **kwargs):
        """Start the application.

        :param app: The config object for the app
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
        sender = os.fsdecode(
            self.binary_path(app) / "Contents" / "MacOS" / app.formal_name
        )
        log_popen = self.subprocess.Popen(
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

        try:
            self.logger.info("Starting app...", prefix=app.app_name)
            try:
                self.subprocess.run(
                    [
                        "open",
                        "-n",  # Force a new app to be launched
                        os.fsdecode(self.binary_path(app)),
                    ],
                    cwd=self.home_path,
                    check=True,
                )
            except subprocess.CalledProcessError:
                raise BriefcaseCommandError(f"Unable to start app {app.app_name}.")

            # Find the App process ID so log streaming can exit when the app exits
            app_pid = get_process_id_by_command(
                command=str(self.binary_path(app)), logger=self.logger
            )
            if app_pid is None:
                self.logger.error()
                self.logger.error(
                    f"Unable to find process for app {app.app_name} to start log streaming."
                )
            else:
                # Start streaming logs for the app.
                self.logger.info(
                    "Following system log output (type CTRL-C to stop log)...",
                    prefix=app.app_name,
                )
                self.logger.info("=" * 75)
                self.subprocess.stream_output(
                    "log stream", log_popen, stop_func=lambda: is_process_dead(app_pid)
                )
        finally:
            self.subprocess.cleanup("log stream", log_popen)


def is_mach_o_binary(path):
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

    def select_identity(self, identity=None):
        """Get the codesigning identity to use.

        :param identity: A pre-specified identity (either the 40-digit
            hex checksum, or the string name of the identity). If provided, it
            will be validated against the list of available identities to
            confirm that it is a valid codesigning identity.
        :returns: The final identity to use
        """
        # Obtain the valid codesigning identities.
        identities = self.get_identities(self, "codesigning")

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
                        f"Invalid code signing identity {identity!r}"
                    ) from e

        if len(identities) == 0:
            raise BriefcaseCommandError("No code signing identities are available.")
        elif len(identities) == 1:
            identity, identity_name = list(identities.items())[0]
        else:
            self.input.prompt()
            self.input.prompt("Select code signing identity to use:")
            self.input.prompt()
            identity = select_option(identities, input=self.input)
            identity_name = identities[identity]
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
        :param identity: The code signing identity to use. Either the 40-digit
            hex checksum, or the string name of the identity.
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

        self.logger.info(f"Signing {Path(path).relative_to(self.base_path)}")
        try:
            self.subprocess.run(
                process_command,
                stderr=subprocess.PIPE,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            errors = e.stderr
            if "code object is not signed at all" in errors:
                self.logger.info("... file requires a deep sign; retrying")
                try:
                    self.subprocess.run(
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
                self.logger.info("... no signature required")
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

        # Sign all Mach-O executable objects
        sign_targets = [
            path
            for path in resources_path.rglob("*")
            if not path.is_dir() and is_mach_o_binary(path)
        ]

        # Sign all embedded frameworks
        sign_targets.extend(resources_path.rglob("*.framework"))

        # Sign all embedded app objets
        sign_targets.extend(resources_path.rglob("*.app"))

        # Sign the bundle path itself
        sign_targets.append(bundle_path)

        # Signs code objects in reversed lexicographic order to ensure nesting order is respected
        # (objects must be signed from the inside out)
        with self.input.progress_bar() as progress_bar:
            task_id = progress_bar.add_task("Signing App", total=len(sign_targets))
            for path in sorted(sign_targets, reverse=True):
                self.sign_file(
                    path,
                    entitlements=self.entitlements_path(app),
                    identity=identity,
                )
                progress_bar.update(task_id, advance=1)


class macOSPackageMixin(macOSSigningMixin):
    @property
    def packaging_formats(self):
        return ["app", "dmg"]

    @property
    def default_packaging_format(self):
        return "dmg"

    def add_options(self, parser):
        super().add_options(parser)
        # We use store_const:False rather than store_false so that the
        # "unspecified" value is None, rather than True, allowing for
        # a "default behavior" interpretation with `--no-sign` or
        # `--adhoc-sign` is specified
        parser.add_argument(
            "--no-notarize",
            dest="notarize_app",
            action="store_const",
            const=False,
            help="Disable notarization for the app",
        )

    def verify_tools(self):
        if self.host_os != "Darwin":
            raise BriefcaseCommandError(
                "Code signing and / or building a DMG requires running on macOS."
            )

        # Require the XCode command line tools.
        verify_command_line_tools_install(self)

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
                "Couldn't extract Team ID from signing identity {identity!r}"
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
                    with ZipFile(archive_filename, "a") as archive:
                        for path in filename.glob("**/*"):
                            archive.write(
                                path, arcname=path.relative_to(filename.parent)
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
                        self.subprocess.run(
                            [
                                "xcrun",
                                "notarytool",
                                "store-credentials",
                                "--team-id",
                                team_id,
                                profile,
                            ],
                            check=True,
                        )
                    except subprocess.CalledProcessError as e:
                        raise BriefcaseCommandError(
                            f"Unable to store credentials for team ID {team_id}."
                        ) from e

                # Attempt the notarization
                try:
                    self.logger.info()
                    self.subprocess.run(
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
            # Clean up house; we don't need the archive any more.
            if archive_filename != filename:
                self.os.unlink(archive_filename)

        try:
            self.logger.info()
            self.logger.info(
                f"Stapling notarization onto {filename.relative_to(self.base_path)}..."
            )
            self.subprocess.run(
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
        app: BaseConfig,
        sign_app=True,
        notarize_app=None,
        identity=None,
        adhoc_sign=False,
        packaging_format="dmg",
        **kwargs,
    ):
        """Package an app bundle.

        :param app: The application to package
        :param sign_app: Should the application be signed? Default: ``True``
        :param notarize_app: Should the app be notarized? Default: ``True`` if the
            app has been signed with a real identity; ``False`` if the app is
            unsigned, or an ad-hoc signing identity has been used.
        :param identity: The code signing identity to use. This can be either
            the 40-digit hex checksum, or the string name of the identity.
            If unspecified, the user will be prompted for a code signing
            identity. Ignored if ``sign_app`` is ``False``.
        :param adhoc_sign: If ``True``, code will be signed with adhoc identity of "-"
        :param packaging_format: The packaging format to use. Default is ``dmg``.
        """
        if sign_app:
            if adhoc_sign:
                if notarize_app:
                    raise BriefcaseCommandError(
                        "Can't notarize an app with an adhoc signing identity"
                    )

                identity = "-"
                self.logger.info(
                    "Signing app with adhoc identity...", prefix=app.app_name
                )
            else:
                # If we're signing, and notarization isn't explicitly disabled,
                # notarize by default.
                if notarize_app is None:
                    notarize_app = True

                identity, identity_name = self.select_identity(identity=identity)

                self.logger.info(
                    f"Signing app with identity {identity_name}...", prefix=app.app_name
                )

                if notarize_app:
                    team_id = self.team_id_from_identity(identity_name)

            self.sign_app(app=app, identity=identity)
        else:
            if notarize_app:
                raise BriefcaseCommandError(
                    "Can't notarize an app that hasn't been signed"
                )

        if packaging_format == "app":
            if notarize_app:
                self.logger.info(
                    f"Notarizing app using team ID {team_id}...",
                    prefix=app.app_name,
                )
                self.notarize(self.binary_path(app), team_id=team_id)

        if packaging_format == "dmg":
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

            dmg_path = self.distribution_path(app, packaging_format=packaging_format)
            self.dmgbuild.build_dmg(
                filename=os.fsdecode(dmg_path),
                volume_name=f"{app.formal_name} {app.version}",
                settings=dmg_settings,
            )

            if sign_app:
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
