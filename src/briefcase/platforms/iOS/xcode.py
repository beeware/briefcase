from __future__ import annotations

import argparse
import contextlib
import json
import plistlib
import re
import subprocess
import time
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NamedTuple
from uuid import UUID

from packaging.version import Version

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import EnvManagerT, FinalizedAppConfig
from briefcase.console import Console
from briefcase.debuggers.base import AppPackagesPathMappings
from briefcase.exceptions import (
    BriefcaseCommandError,
    InputDisabled,
    InvalidDeviceError,
    NoDistributionArtefact,
)
from briefcase.integrations.subprocess import is_process_dead
from briefcase.integrations.virtual_environment import VirtualEnvironment
from briefcase.integrations.xcode import (
    DeviceState,
    get_device_state,
    get_identities,
    get_physical_devices,
    get_simulators,
    get_team_id,
)
from briefcase.platforms.iOS import iOSMixin
from briefcase.platforms.macOS.filters import (
    XcodeBuildFilter,
    macOS_log_clean_filter,
    nslog_clean_filter,
)

# The name prefixes of the signing identities that can be used to deploy to a
# physical device. "iPhone Developer" is the name used by older certificates.
DEVELOPMENT_IDENTITY_PREFIXES = ("Apple Development:", "iPhone Developer:")


class iOSDevice(NamedTuple):
    """A device (simulator or physical) that can run an iOS app."""

    udid: str
    os_version: str
    name: str
    physical: bool


@dataclass
class iOSSigningIdentity:
    """A signing identity for deploying an app to a physical iOS device."""

    id: str
    name: str
    team_id: str


class iOSXcodePassiveMixin(iOSMixin):
    output_format = "Xcode"
    supported_env_managers: Collection[EnvManagerT] = {"venv", "uv"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # The device the app will run on, and (for a physical device) the
        # identity used to sign the app. These are selected by the run command.
        self.target_device: iOSDevice | None = None
        self.signing_identity: iOSSigningIdentity | None = None

    def clone_options(self, command):
        """Clone the target device and signing identity."""
        super().clone_options(command)
        self.target_device = command.target_device
        self.signing_identity = command.signing_identity

    @property
    def packaging_formats(self):
        return ["ipa"]

    @property
    def default_packaging_format(self):
        return "ipa"

    def project_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.xcodeproj"

    def binary_path(self, app):
        if self.target_device and self.target_device.physical:
            sdk = "iphoneos"
        else:
            sdk = "iphonesimulator"
        return (
            self.bundle_path(app) / "build" / f"Debug-{sdk}" / f"{app.formal_name}.app"
        )

    def distribution_path(self, app):
        # This path won't ever be *generated*, as distribution artefacts
        # can't be generated on iOS.
        raise NoDistributionArtefact(
            Console.format_warning_banner(
                title="No distributable artefact has been generated",
                message="""\
                    Briefcase has not generated a standalone iOS artefact, as
                    iOS apps must be published through Xcode.

                    To open Xcode for your iOS project, run:

                        briefcase open iOS

                    and use Xcode's app distribution workflow described at:

                        https://briefcase.readthedocs.io/en/stable/reference/platforms/iOS/xcode.html#ios-deploy
                """,
            )
        )


class iOSXcodeMixin(iOSXcodePassiveMixin):
    # The default value of the -d/--device option.
    default_device = "auto"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External service APIs.
        # These are abstracted to enable testing without patching.
        self.get_simulators = get_simulators
        self.get_physical_devices = get_physical_devices
        self.get_identities = get_identities
        self.get_team_id = get_team_id

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "-d",
            "--device",
            dest="udid",
            nargs="?",
            default=self.default_device,
            const=None,
            help=(
                "The device to target; either a UDID, a device name "
                '("iPhone 11"), a device name and OS version '
                '("iPhone 11::iOS 13.3"), or "auto" (the default) to '
                'automatically select a recent "SE-class" device on the '
                "most recently released iOS version. Provide -d with no "
                "value to select from the full list of available "
                "simulators and connected physical devices."
            ),
            required=False,
        )

    def add_identity_option(self, parser):
        """Add the option to specify the signing identity for a physical device.

        :param parser: a stub argparse parser for the command.
        """
        parser.add_argument(
            "-i",
            "--identity",
            dest="identity",
            help=(
                "The development signing identity to use when running on a "
                "physical device; either the 40-digit hex checksum, or the "
                "full name of the identity."
            ),
            required=False,
        )

    def prepare_target(
        self,
        app: FinalizedAppConfig,
        *,
        udid: str | None = None,
        identity: str | None = None,
        **options,
    ) -> bool:
        """Select the device to run on and, for a physical device, the signing identity
        to use.

        :param app: The config object for the app
        :param udid: The device UDID, name, or name::version to target. If
            `"auto"`, a recent "SE-class" simulator on the most recent iOS
            version will be selected automatically. If `None`, the user will
            be asked to select a device at runtime.
        :param identity: The signing identity to use for a physical device. If
            `None`, the user will be asked to select an identity.
        :returns: True if the app must be built; a physical device always
            requires a build, so that Xcode can sign the app with the selected
            identity.
        """
        try:
            self.target_device = self.select_target_device(udid)
            if self.target_device.physical:
                self.signing_identity = self.select_identity(identity)
        except InputDisabled as e:
            raise BriefcaseCommandError(
                "Input has been disabled; can't select a device or signing "
                "identity. Use -d/--device to specify the device and, for a "
                "physical device, -i/--identity to specify the signing identity."
            ) from e

        return self.target_device.physical

    def select_target_device(self, udid_or_device=None):
        """Select the target device to use for iOS builds.

        Interrogates the system to get the list of available simulators, and
        the physical devices connected to this machine.

        If the user has specified "auto", a recent "SE-class" iPhone simulator
        is selected automatically, on the most recent iOS version, without
        prompting.

        If there is only a single iOS version available, that version
        will be selected automatically.

        If there is only one simulator available, that version will be selected
        automatically.

        If the user has specified a device at the command line, it will be
        used in preference to any of the above.

        :param udid_or_device: The device to target. Can be:
            - `None` (default if -d/--device was specified with no value)
            - The literal string `"auto"` (case-insensitive); automatically
              select a recent "SE-class" simulator on the most recent
              available iOS version, without prompting.
            - A device UUID.
            - A device name (e.g. `"iPhone 11"`).
            - A device name and OS version (e.g. `"iPhone 11::iOS 13.3"`).
        :returns: The selected device.
        """
        simulators = self.get_simulators(self.tools, "iOS")

        # Physical devices are candidates for any selection other than "auto".
        if udid_or_device is None or udid_or_device.lower() != "auto":
            physical_devices = self.get_physical_devices(self.tools, "iOS")
        else:
            physical_devices = {}

        # Combine the simulators and physical devices, grouped by iOS version.
        targets = {
            iOS_tag: {
                **simulators.get(iOS_tag, {}),
                **physical_devices.get(iOS_tag, {}),
            }
            for iOS_tag in simulators | physical_devices
        }
        physical_udids = {
            udid for devices in physical_devices.values() for udid in devices
        }

        try:
            # Try to convert to a UDID. If this succeeds, then the argument
            # is a UDID.
            udid = str(UUID(udid_or_device)).upper()
            # User has provided a UDID at the command line; look for it.
            for iOS_tag, devices in targets.items():
                try:
                    device = devices[udid]
                    # iOS_tag will be of the form "iOS 15.5"
                    # Drop the "iOS" prefix when reporting the version.
                    iOS_version = iOS_tag.split(" ", 1)[-1]
                    return iOSDevice(udid, iOS_version, device, udid in physical_udids)
                except KeyError:
                    # UDID doesn't exist in this iOS version; try another.
                    pass

            # We've iterated through all available iOS versions and
            # found no match; return an error.
            raise InvalidDeviceError("device UDID", udid)

        except (ValueError, TypeError) as e:
            # Provided value wasn't a UDID.
            if udid_or_device and udid_or_device.lower() == "auto":
                # No -d/--device value, or "-d auto": automatically select a
                # recent "SE-class" device on the most recent iOS version,
                # without prompting.
                if not simulators:
                    raise BriefcaseCommandError("No iOS simulators available.") from e

                # simulators is keyed by iOS version tags of the form
                # "iOS 15.5"; pick the tag with the highest version number.
                iOS_tag = max(
                    simulators,
                    key=lambda tag: tuple(int(v) for v in tag.split()[-1].split(".")),
                )
                devices = simulators[iOS_tag]

                matches = [
                    (candidate_udid, name)
                    for candidate_udid, name in devices.items()
                    if name.startswith("iPhone SE ")
                    or (name.startswith("iPhone ") and name.endswith("e"))
                ]
                if matches:
                    # If multiple SE-class devices match, pick
                    # deterministically (alphabetically last device name).
                    udid, device = max(matches, key=lambda item: item[1])
                else:
                    raise BriefcaseCommandError(
                        "Unable to automatically select an iOS simulator; "
                        'no "SE-class" iPhone simulator (e.g., an iPhone SE, '
                        'or a similar "entry level" device) is available on '
                        f"{iOS_tag}, and the choice is ambiguous.\n"
                        "\n"
                        "Specify a device explicitly with -d/--device, or use "
                        "-d with no value to select from the full list of "
                        "available simulators."
                    ) from e

                # iOS_tag will be of the form "iOS 15.5"
                # Drop the "iOS" prefix when reporting the version.
                iOS_version = iOS_tag.split(" ", 1)[-1]
                self.console.info(
                    f"Automatically selected {device} simulator on {iOS_tag}"
                )
                return iOSDevice(udid, iOS_version, device, udid in physical_udids)
            elif udid_or_device and "::" in udid_or_device:
                # A device name::version.
                device, iOS_tag = udid_or_device.split("::")

                try:
                    # Convert the simulator dict into a dict where
                    # the iOS versions are lower cased, then do a lookup
                    # on the lower case name provided by the user.
                    # However, also return the *unmodified* iOS version string
                    # so we can convert the user-provided iOS version into the
                    # "clean", official capitalization.
                    iOS_tag, devices = {
                        clean_iOS_tag.lower(): (clean_iOS_tag, details)
                        for clean_iOS_tag, details in targets.items()
                    }[iOS_tag.lower()]

                    # iOS_tag will be of the form "iOS 15.5"
                    # Drop the "iOS" prefix when reporting the version.
                    iOS_version = iOS_tag.split(" ", 1)[-1]
                    try:
                        # Do a reverse lookup for UDID, based on a
                        # case-insensitive name lookup.
                        udid = {name.lower(): udid for udid, name in devices.items()}[
                            device.lower()
                        ]

                        # Found a match;
                        # normalize back to the official name and return.
                        device = devices[udid]
                        return iOSDevice(
                            udid, iOS_version, device, udid in physical_udids
                        )
                    except KeyError as e:
                        raise InvalidDeviceError("device name", device) from e
                except KeyError as e:
                    raise InvalidDeviceError("iOS Version", iOS_tag) from e
            elif udid_or_device:
                # Physical device UDIDs aren't UUIDs; check for a match on
                # a physical device UDID before treating it as a device name.
                for iOS_tag, devices in physical_devices.items():
                    udid = udid_or_device.upper()
                    if udid in devices:
                        # iOS_tag will be of the form "iOS 15.5"
                        # Drop the "iOS" prefix when reporting the version.
                        iOS_version = iOS_tag.split(" ", 1)[-1]
                        return iOSDevice(
                            udid, iOS_version, devices[udid], physical=True
                        )

                # Just a device name
                device = udid_or_device

                # Search iOS versions, looking for most recent version first.
                # The iOS tag will be something like "iOS 15.4";
                # Drop the prefix (if it exists), convert into the tuple (15, 4),
                # and sort numerically.
                for iOS_tag, devices in sorted(
                    targets.items(),
                    key=lambda item: tuple(
                        int(v) for v in item[0].split()[-1].split(".")
                    ),
                    reverse=True,
                ):
                    try:
                        udid = {name.lower(): udid for udid, name in devices.items()}[
                            device.lower()
                        ]

                        # Found a match;
                        # normalize back to the official name and return.
                        device = devices[udid]

                        # iOS_tag will be of the form "iOS 15.5"
                        # Drop the "iOS" prefix when reporting the version.
                        iOS_version = iOS_tag.split(" ", 1)[-1]

                        return iOSDevice(
                            udid, iOS_version, device, udid in physical_udids
                        )
                    except KeyError:
                        # UDID doesn't exist in this iOS version; try another.
                        pass
                raise InvalidDeviceError("device name", device) from e

        if len(targets) == 0:
            raise BriefcaseCommandError("No iOS simulators available.")
        elif len(targets) == 1:
            iOS_tag = next(iter(targets.keys()))
        else:
            iOS_tag = self.console.selection_question(
                intro="Select iOS version:",
                description="iOS Version",
                options=targets.keys(),
            )

        devices = targets[iOS_tag]

        if len(devices) == 0:
            raise BriefcaseCommandError(f"No simulators available for {iOS_tag}.")
        elif len(devices) == 1:
            udid = next(iter(devices.keys()))
        else:
            udid = self.console.selection_question(
                intro="Select simulator device to use:",
                description="Simulator",
                options={
                    udid: (
                        f"{name} (physical device)" if udid in physical_udids else name
                    )
                    for udid, name in devices.items()
                },
            )

        device = devices[udid]

        self.console.info(f"""
In the future, you could specify this device by running:

    $ briefcase {self.command} iOS -d "{device}::{iOS_tag}"

or:

    $ briefcase {self.command} iOS -d {udid}
""")

        # iOS_tag will be of the form "iOS 15.5"
        # Drop the "iOS" prefix when reporting the version.
        iOS_version = iOS_tag.split(" ", 1)[-1]

        return iOSDevice(udid, iOS_version, device, udid in physical_udids)

    def select_identity(self, identity: str | None = None) -> iOSSigningIdentity:
        """Select the signing identity to use when deploying to a physical device.

        :param identity: A pre-specified identity (either the 40-digit hex checksum, or
            the name of the identity). If not provided, the user will be asked to select
            an identity.
        :returns: The signing identity to use.
        """
        identities = {
            identity_id: name
            for identity_id, name in self.get_identities(
                self.tools, "codesigning"
            ).items()
            if name.startswith(DEVELOPMENT_IDENTITY_PREFIXES)
        }
        if not identities:
            raise BriefcaseCommandError(
                "No development signing identities are available. Deploying to "
                "a physical device requires an Apple Development certificate, "
                "and its private key, to be installed in your keychain. See:\n"
                "\n"
                "    https://briefcase.beeware.org/en/stable/how-to/code-signing/iOS/\n"
                "\n"
                "for details on how to obtain a development certificate."
            )

        if identity is None:
            identity_id = self.console.selection_question(
                intro="Select development signing identity to use:",
                description="Development Signing Identity",
                options=identities,
            )
        elif identity in identities:
            identity_id = identity
        else:
            matches = [
                identity_id
                for identity_id, name in identities.items()
                if name == identity
            ]
            if not matches:
                raise BriefcaseCommandError(
                    f"Invalid development signing identity {identity!r}."
                )
            elif len(matches) > 1:
                raise BriefcaseCommandError(
                    f"More than one signing identity is named {identity!r}. "
                    "Specify the identity using one of these fingerprints:\n\n"
                    + "\n".join(f"    {match}" for match in matches)
                )
            identity_id = matches[0]
        name = identities[identity_id]

        return iOSSigningIdentity(
            id=identity_id,
            name=name,
            team_id=self.get_team_id(self.tools, identity_id, name),
        )


class iOSXcodeCreateCommand(iOSXcodePassiveMixin, CreateCommand):
    description = "Create and populate a iOS Xcode project."
    app_template_hash = "sha1:2d6805fe1d02b6c46197366d36cac97415cf101b"

    def support_package_url(self, support_revision: str) -> str:
        """The URL of the support package to use for apps of this type."""
        # Official CPython iOS support packages are available from 3.15.0b1
        if self.tools.sys.version_info < (3, 15):  # pramga: no-cover-if-gte-py315
            return super().support_package_url(support_revision)
        else:  # pramga: no-cover-if-lt-py315
            micro = re.match(r"\d+", str(support_revision)).group(0)
            return (
                "https://www.python.org/ftp/python/"
                f"{self.python_version_tag}.{micro}/"
                f"python-{self.python_version_tag}.{support_revision}-iOS-XCframework.tar.gz"
            )

    def permissions_context(
        self,
        app: FinalizedAppConfig,
        x_permissions: dict[str, str],
    ):
        """Additional template context for permissions.

        :param app: The config object for the app
        :param x_permissions: The dictionary of known cross-platform permission
            definitions.
        :returns: The template context describing permissions for the app.
        """
        # The collection of info.plist entries
        info = {}

        if x_permissions["bluetooth"]:
            info["NSBluetoothAlwaysUsageDescription"] = x_permissions["bluetooth"]
        if x_permissions["camera"]:
            info["NSCameraUsageDescription"] = x_permissions["camera"]
        if x_permissions["microphone"]:
            info["NSMicrophoneUsageDescription"] = x_permissions["microphone"]

        if x_permissions["fine_location"]:
            info["NSLocationWhenInUseUsageDescription"] = x_permissions["fine_location"]
            info["NSLocationDefaultAccuracyReduced"] = False
        elif x_permissions["coarse_location"]:
            info["NSLocationWhenInUseUsageDescription"] = x_permissions[
                "coarse_location"
            ]
            info["NSLocationDefaultAccuracyReduced"] = True

        if x_permissions["background_location"]:
            if "NSLocationWhenInUseUsageDescription" not in info:
                info["NSLocationWhenInUseUsageDescription"] = x_permissions[
                    "background_location"
                ]
            info["NSLocationAlwaysAndWhenInUseUsageDescription"] = x_permissions[
                "background_location"
            ]
            info["UIBackgroundModes"] = ["processing", "location"]

        if x_permissions["photo_library"]:
            info["NSPhotoLibraryAddUsageDescription"] = x_permissions["photo_library"]

        # Override any info.plist entries with the platform specific definitions
        info.update(getattr(app, "info", {}))

        return {
            "info": info,
        }

    def create_app_environment(
        self,
        app: FinalizedAppConfig,
        platform: str,
        arch: str,
        env_manager: EnvManagerT | Literal["default"] | None = "default",
        recreate: bool = True,
    ):
        """Create an isolated iOS virtual environment in which the app can be built.

        :param app: The config object for the app
        :param platform: The platform being targeted.
        :param arch: The architecture for the environment.
        :param env_manager: An explicit environment manager to use. Defaults to the
            app's configured environment manager.
        :param recreate: If the environment already exists, should it be re-created?
            Defaults to True (i.e., recreate by default).
        """
        # The default invocation will be with self.platform, which will be "iOS".
        # Interpret that as the device; interpret all others as simulators.
        if platform == "iOS":
            platform = "iphoneos"

        return super().create_app_environment(
            app=app,
            platform=platform,
            arch=arch,
            env_manager=env_manager,
            recreate=recreate,
            support_path=self.support_path(app),
        )

    def _install_app_requirements(
        self,
        app: FinalizedAppConfig,
        venv: VirtualEnvironment,
        requires: list[str],
        app_packages_path: Path,
    ):
        try:
            # Determine the min iOS version from the framework metadata
            # of the ios-arm64 slice of the XCframework
            plist_file = (
                self.support_path(app)
                / "Python.xcframework/ios-arm64/Python.framework/Info.plist"
            )
            with plist_file.open("rb") as f:
                info_plist = plistlib.load(f)

            support_min_version = info_plist["MinimumOSVersion"]
        except KeyError:
            raise BriefcaseCommandError(
                "Your iOS XCframework doesn't specify a minimum iOS version."
            ) from None
        except FileNotFoundError:
            # If a plist file couldn't be found, it's an old-style support package;
            # Determine min. iOS version from the VERSIONS file in the support package
            versions = dict(
                [part.strip() for part in line.split(": ", 1)]
                for line in (
                    (self.support_path(app) / "VERSIONS")
                    .read_text(encoding="UTF-8")
                    .split("\n")
                )
                if ": " in line
            )
            support_min_version = versions.get("Min iOS version", "13.0")

        # Check that the app's definition is compatible with the support package.
        # If the app doesn't specify a minimum version, use the support package
        # minimum version as a default.
        ios_min_version = getattr(app, "min_os_version", support_min_version)

        if Version(ios_min_version) < Version(support_min_version):
            raise BriefcaseCommandError(
                f"Your iOS app specifies a minimum iOS version of {ios_min_version}, "
                f"but the support package only supports {support_min_version}"
            )

        # Perform the initial install pass targeting the "iphoneos" platform
        with (
            self.console.wait_bar("Installing app requirements for iPhone device..."),
        ):
            venv.install_requirements(
                requires,
                allow_editable=False,
                require_binary=self.require_binary_installs,
                min_os_version=ios_min_version,
                extra_installer_args=app.requirement_installer_args,
                install_path=app_packages_path.parent / "app_packages.iphoneos",
                install_hint=f"""

This may be because the `iphoneos` wheels that are available are not compatible
with Python {self.python_version_tag} and a minimum iOS version of {ios_min_version}.
""",
            )

        # Perform a second install pass targeting the iOS simulator platform for the
        # current architecture
        sim_venv = self.create_app_environment(
            app,
            platform="iphonesimulator",
            arch=self.tools.host_arch,
        )
        with (
            self.console.wait_bar(
                "Installing app requirements for iPhone simulator..."
            ),
        ):
            sim_venv.install_requirements(
                requires,
                allow_editable=False,
                require_binary=self.require_binary_installs,
                min_os_version=ios_min_version,
                extra_installer_args=app.requirement_installer_args,
                install_path=app_packages_path.parent / "app_packages.iphonesimulator",
                install_hint=f"""

This may indicate that an `iphoneos` wheel could be found, but an
`iphonesimulator` wheel could not be found; or that the `iphonesimulator`
binary wheels that are available are not compatible with
Python {self.python_version_tag} and a minimum iOS version of {ios_min_version}.
""",
            )


class iOSXcodeUpdateCommand(iOSXcodeCreateCommand, UpdateCommand):
    description = "Update an existing iOS Xcode project."
    supports_debugger = True


class iOSXcodeOpenCommand(iOSXcodePassiveMixin, OpenCommand):
    description = "Open an existing iOS Xcode project."


class iOSXcodeBuildCommand(iOSXcodeMixin, BuildCommand):
    description = "Build an iOS Xcode project."
    supports_debugger = True

    # Unless a device is requested, build for the simulator without selecting
    # a device.
    default_device = argparse.SUPPRESS

    def add_options(self, parser):
        super().add_options(parser)
        self.add_identity_option(parser)

    def info_plist_path(self, app: FinalizedAppConfig):
        """Obtain the path to the application's plist file.

        :param app: The config object for the app
        :return: The full path of the application's plist file.
        """
        return self.bundle_path(app) / self.path_index(app, "info_plist_path")

    def update_app_metadata(self, app: FinalizedAppConfig):
        with self.console.wait_bar("Setting main module..."):
            # Load the original plist
            with self.info_plist_path(app).open("rb") as f:
                info_plist = plistlib.load(f)

            # Set the name of the app's main module; this will depend
            # on whether we're in test mode.
            info_plist["MainModule"] = app.main_module()

            # Write the modified plist
            with self.info_plist_path(app).open("wb") as f:
                plistlib.dump(info_plist, f)

    def build_app(self, app: FinalizedAppConfig, **kwargs):
        """Build the Xcode project for the application.

        :param app: The application to build
        """
        # If a device was requested, and it hasn't already been selected (by
        # the run command), select it now.
        if self.target_device is None and "udid" in kwargs:
            self.prepare_target(app, **kwargs)

        if self.target_device and self.target_device.physical:
            # Xcode manages provisioning, using the Apple ID for the selected
            # identity's team. The template uses automatic signing, so the
            # certificate is selected by Xcode, based on the team. The run
            # destination (which determines the SDK and architecture, and is
            # needed to register the device) is only honored when a scheme is
            # provided; building with a scheme also requires an explicit
            # SYMROOT to retain the usual location for the built app.
            target_args = [
                "-scheme",
                app.formal_name,
                "-destination",
                f"id={self.target_device.udid}",
                "-allowProvisioningUpdates",
                "-allowProvisioningDeviceRegistration",
                f"DEVELOPMENT_TEAM={self.signing_identity.team_id}",
                f"SYMROOT={self.bundle_path(app) / 'build'}",
            ]
        else:
            target_args = [
                "-arch",
                self.tools.host_arch,
                "-sdk",
                "iphonesimulator",
            ]
        self.console.info("Updating app metadata...", prefix=app.app_name)
        self.update_app_metadata(app=app)

        self.console.info("Building Xcode project...", prefix=app.app_name)
        with self.console.wait_bar("Building..."):
            try:
                self.tools.subprocess.run(
                    [
                        "xcodebuild",
                        "build",
                        "-project",
                        self.project_path(app),
                        "-configuration",
                        "Debug",
                        *target_args,
                        "-verbose" if self.tools.console.is_deep_debug else "-quiet",
                    ],
                    check=True,
                    filter_func=(
                        None if self.tools.console.is_deep_debug else XcodeBuildFilter()
                    ),
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to build app {app.app_name}."
                ) from e


class iOSXcodeRunCommand(iOSXcodeMixin, RunCommand):
    description = "Run an iOS Xcode project."
    supports_debugger = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External service APIs.
        # This is abstracted to enable testing without patching.
        self.get_device_state = get_device_state

    def debugger_app_packages_path_mapping(
        self,
        app: FinalizedAppConfig,
    ) -> AppPackagesPathMappings:
        """Get the path mappings for the app packages.

        :param app: The config object for the app
        :returns: The path mappings for the app packages
        """
        sdk = "iphoneos" if self.target_device.physical else "iphonesimulator"
        return AppPackagesPathMappings(
            sys_path_regex="app_packages$",
            host_folder=str(self.app_packages_path(app).parent / f"app_packages.{sdk}"),
        )

    def add_options(self, parser):
        super().add_options(parser)
        self.add_identity_option(parser)

    def run_app(
        self,
        app: FinalizedAppConfig,
        *,
        passthrough: list[str],
        **options,
    ) -> dict | None:
        """Start the application.

        :param app: The config object for the app
        :param passthrough: The list of arguments to pass to the app
        """
        udid, iOS_version, device, _ = self.target_device

        if app.test_mode:
            label = "test suite"
        else:
            label = "app"

        self.console.info(
            (
                f"Starting {label} on an {device} running iOS {iOS_version} "
                f"(device UDID {udid})"
            ),
            prefix=app.app_name,
        )

        # Add additional environment variables
        env = {}
        if app.debugger:
            env["BRIEFCASE_DEBUGGER"] = app.debugger.get_env_config(self, app)

        if self.target_device.physical:
            self._run_app_on_device(app, label=label, passthrough=passthrough, env=env)
            return {"udid": udid}

        # The simulator needs to be booted before being started.
        # If it's shut down, we can boot it again; but if it's currently
        # shutting down, we need to wait for it to shut down before restarting.
        device_state = self.get_device_state(self.tools, udid)
        if device_state not in {DeviceState.SHUTDOWN, DeviceState.BOOTED}:
            with self.console.wait_bar("Waiting for simulator shutdown..."):
                while device_state not in {DeviceState.SHUTDOWN, DeviceState.BOOTED}:
                    time.sleep(2)
                    device_state = self.get_device_state(self.tools, udid)

        # We now know the simulator is either shut down or booted;
        # if it's shut down, start it again.
        if device_state == DeviceState.SHUTDOWN:
            try:
                with self.console.wait_bar("Booting simulator..."):
                    self.tools.subprocess.run(
                        ["xcrun", "simctl", "boot", udid],
                        check=True,
                    )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to boot {device} simulator running {iOS_version}"
                ) from e

        device_hub_started = False
        if not app.test_mode:
            # We now know the simulator is *running*, so we can open it.
            # We don't need to open the simulator to run the test suite.
            try:
                with self.console.wait_bar("Opening simulator..."):
                    if self.tools.xcode.version < Version("27.0"):
                        self.tools.subprocess.run(
                            [
                                "open",
                                "-a",
                                "Simulator",
                                "--args",
                                "-CurrentDeviceUDID",
                                udid,
                            ],
                            check=True,
                        )
                    else:
                        self.tools.subprocess.run(
                            ["open", "-a", "Device Hub"],
                            check=True,
                        )
                        device_hub_started = True
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to open {device} simulator running {iOS_version}"
                ) from e

        # Try to uninstall the app first. If the app hasn't been installed
        # before, this will still succeed.
        self.console.info(f"Installing {label}...", prefix=app.app_name)
        with (
            self.console.wait_bar(
                "Uninstalling any existing app version..."
            ) as keep_alive,
            self.tools.subprocess.Popen(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    udid,
                    app.bundle_identifier,
                ]
            ) as uninstall_popen,
        ):
            while (ret_code := uninstall_popen.poll()) is None:
                keep_alive.update()
                time.sleep(0.25)
        if ret_code != 0:
            self.console.error(f"{ret_code=}")
            raise BriefcaseCommandError(
                f"Unable to uninstall old version of app {app.app_name}."
            )

        # Install the app.
        with (
            self.console.wait_bar(f"Installing new {label} version...") as keep_alive,
            self.tools.subprocess.Popen(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    udid,
                    self.binary_path(app),
                ]
            ) as install_popen,
        ):
            while (ret_code := install_popen.poll()) is None:
                keep_alive.update()
                time.sleep(0.25)
        if ret_code != 0:
            raise BriefcaseCommandError(
                f"Unable to install new version of app {app.app_name}."
            )

        # Start log stream for the app.
        # The following sets up a log stream filter that looks for:
        #  1. a log sender that matches that app binary; or,
        #  2. a log sender of that is a Python extension module,
        #     and a process that matches the app binary.
        # Case (1) works when the standard library is statically linked,
        #   and for native NSLog() calls in the bootstrap binary
        # Case (2) works when the standard library is dynamically linked,
        #   and ctypes (which handles the NSLog integration) is an
        #   extension module. It also catches the case for the CPython
        #   builtin behavior of redirecting to the system log.
        # It's not enough to filter on *just* the processImagePath,
        # as the process will generate lots of system-level messages.
        # We can't filter on *just* the senderImagePath, because other
        # apps will generate log messages that would be caught by the filter.
        simulator_log_popen = self.tools.subprocess.Popen(
            [
                "xcrun",
                "simctl",
                "spawn",
                udid,
                "log",
                "stream",
                "--style",
                "compact",
                "--predicate",
                (
                    f'senderImagePath ENDSWITH "/{app.formal_name}"'
                    f'OR (processImagePath ENDSWITH "/{app.formal_name}"'
                    '  AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                    '    OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                    '    OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"'
                    '    OR senderImagePath ENDSWITH "/Python"'
                    "  )"
                    ")"
                ),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )

        # Wait for the log stream start up
        time.sleep(0.25)

        # Set additional environment variables while the app is running
        # (no-op if no environment variables are set).
        with self.setup_env(env, udid):
            try:
                self.console.info(f"Starting {label}...", prefix=app.app_name)
                with self.console.wait_bar(f"Launching {label}..."):
                    output = self.tools.subprocess.check_output(
                        [
                            "xcrun",
                            "simctl",
                            "launch",
                            udid,
                            app.bundle_identifier,
                            *passthrough,
                        ]
                    )
                    try:
                        app_pid = int(output.split(":")[1].strip())
                    except (IndexError, ValueError) as e:
                        raise BriefcaseCommandError(
                            f"Unable to determine PID of {label} {app.app_name}."
                        ) from e

                if device_hub_started:
                    self.console.warning(
                        "Device Hub has been started. You may need to select "
                        f"the {device} device running iOS {iOS_version} in the GUI."
                    )

                # Start streaming logs for the app.
                self.console.info(
                    "Following simulator log output (type CTRL-C to stop log)...",
                    prefix=app.app_name,
                )

                # Stream the app logs,
                self._stream_app_logs(
                    app,
                    popen=simulator_log_popen,
                    clean_filter=macOS_log_clean_filter,
                    clean_output=True,
                    stop_func=lambda: is_process_dead(app_pid),
                    log_stream=True,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to launch {label} {app.app_name}."
                ) from e

        # Preserve the device selection as state.
        return {"udid": udid}

    def _run_app_on_device(
        self,
        app: FinalizedAppConfig,
        label: str,
        passthrough: list[str],
        env: dict[str, str],
    ):
        """Install and start the application on a physical device.

        :param app: The config object for the app
        :param label: The label describing what is being run
        :param passthrough: The list of arguments to pass to the app
        :param env: Additional environment variables for the app
        """
        udid = self.target_device.udid
        try:
            with self.console.wait_bar(f"Installing new {label} version..."):
                self.tools.subprocess.run(
                    [
                        "xcrun",
                        "devicectl",
                        "device",
                        "install",
                        "app",
                        "-q",
                        "--device",
                        udid,
                        self.binary_path(app),
                    ],
                    check=True,
                )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to install new version of app {app.app_name}."
            ) from e

        # Launch the app with the console attached, so that the app's output
        # is streamed until the app exits. The app's launcher sends Python
        # output to the console (rather than the system log) when requested.
        self.console.info(f"Starting {label}...", prefix=app.app_name)
        launch_popen = self.tools.subprocess.Popen(
            [
                "xcrun",
                "devicectl",
                "device",
                "process",
                "launch",
                "-q",
                "--device",
                udid,
                "--console",
                "--terminate-existing",
                "--environment-variables",
                json.dumps({"BRIEFCASE_CONSOLE_OUTPUT": "1", **env}),
                app.bundle_identifier,
                *passthrough,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )

        self.console.info(
            "Following device console output (type CTRL-C to stop)...",
            prefix=app.app_name,
        )
        self._stream_app_logs(
            app,
            popen=launch_popen,
            clean_filter=nslog_clean_filter,
            clean_output=True,
        )

    @contextlib.contextmanager
    def setup_env(
        self,
        env: dict[str, str] | None,
        udid: str,
    ):
        """Context manager to set up the environment for the command."""
        if env:
            with self.console.wait_bar("Setting environment variables in simulator..."):
                for env_key, env_value in env.items():
                    self.tools.subprocess.check_output(
                        [
                            "xcrun",
                            "simctl",
                            "spawn",
                            udid,
                            "launchctl",
                            "setenv",
                            f"{env_key}",
                            f"{env_value}",
                        ]
                    )

            yield

            with self.console.wait_bar(
                "Removing environment variables from simulator..."
            ):
                for env_key in env:
                    self.tools.subprocess.check_output(
                        [
                            "xcrun",
                            "simctl",
                            "spawn",
                            udid,
                            "launchctl",
                            "unsetenv",
                            f"{env_key}",
                        ]
                    )
        else:
            yield  # no-op if no environment variables are set


class iOSXcodePackageCommand(iOSXcodeMixin, PackageCommand):
    description = "Package an iOS app."


class iOSXcodePublishCommand(iOSXcodeMixin, PublishCommand):
    description = "Publish an iOS app."


# Declare the briefcase command bindings
create = iOSXcodeCreateCommand
update = iOSXcodeUpdateCommand
open = iOSXcodeOpenCommand
build = iOSXcodeBuildCommand
run = iOSXcodeRunCommand
package = iOSXcodePackageCommand
publish = iOSXcodePublishCommand
