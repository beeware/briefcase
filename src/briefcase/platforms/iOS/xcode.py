from __future__ import annotations

import plistlib
import subprocess
import time
from pathlib import Path
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
from briefcase.config import AppConfig
from briefcase.exceptions import (
    BriefcaseCommandError,
    InputDisabled,
    InvalidDeviceError,
    NoDistributionArtefact,
)
from briefcase.integrations.subprocess import is_process_dead
from briefcase.integrations.xcode import DeviceState, get_device_state, get_simulators
from briefcase.platforms.iOS import iOSMixin
from briefcase.platforms.macOS.filters import XcodeBuildFilter, macOS_log_clean_filter


class iOSXcodePassiveMixin(iOSMixin):
    output_format = "Xcode"

    @property
    def packaging_formats(self):
        return ["ipa"]

    @property
    def default_packaging_format(self):
        return "ipa"

    def project_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.xcodeproj"

    def binary_path(self, app):
        return (
            self.bundle_path(app)
            / "build"
            / "Debug-iphonesimulator"
            / f"{app.formal_name}.app"
        )

    def distribution_path(self, app):
        # This path won't ever be *generated*, as distribution artefacts
        # can't be generated on iOS.
        raise NoDistributionArtefact(
            """
*************************************************************************
** WARNING: No distributable artefact has been generated               **
*************************************************************************

    Briefcase has not generated a standalone iOS artefact, as iOS apps
    must be published through Xcode.

    To open Xcode for your iOS project, run:

        briefcase open iOS

    and use Xcode's app distribution workflow described at:

        https://briefcase.readthedocs.io/en/stable/reference/platforms/iOS/xcode.html#ios-deploy

*************************************************************************
"""
        )


class iOSXcodeMixin(iOSXcodePassiveMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External service APIs.
        # These are abstracted to enable testing without patching.
        self.get_simulators = get_simulators

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "-d",
            "--device",
            dest="udid",
            help="The device to target; either a UDID, "
            'a device name ("iPhone 11"), '
            'or a device name and OS version ("iPhone 11::iOS 13.3")',
            required=False,
        )

    def select_target_device(self, udid_or_device=None):
        """Select the target device to use for iOS builds.

        Interrogates the system to get the list of available simulators

        If there is only a single iOS version available, that version
        will be selected automatically.

        If there is only one simulator available, that version will be selected
        automatically.

        If the user has specified a device at the command line, it will be
        used in preference to any

        :param udid_or_device: The device to target. Can be a device UUID, a
            device name ("iPhone 11"), or a device name and OS version
            ("iPhone 11::13.3"). If ``None``, the user will be asked to select
            a device at runtime.
        :returns: A tuple containing the udid, iOS version, and device name
            for the selected device.
        """
        simulators = self.get_simulators(self.tools, "iOS")
        try:
            # Try to convert to a UDID. If this succeeds, then the argument
            # is a UDID.
            udid = str(UUID(udid_or_device)).upper()
            # User has provided a UDID at the command line; look for it.
            for iOS_tag, devices in simulators.items():
                try:
                    device = devices[udid]
                    # iOS_tag will be of the form "iOS 15.5"
                    # Drop the "iOS" prefix when reporting the version.
                    iOS_version = iOS_tag.split(" ", 1)[-1]
                    return udid, iOS_version, device
                except KeyError:
                    # UDID doesn't exist in this iOS version; try another.
                    pass

            # We've iterated through all available iOS versions and
            # found no match; return an error.
            raise InvalidDeviceError("device UDID", udid)

        except (ValueError, TypeError) as e:
            # Provided value wasn't a UDID.
            # It must be a device or device+version
            if udid_or_device and "::" in udid_or_device:
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
                        for clean_iOS_tag, details in simulators.items()
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
                        return udid, iOS_version, device
                    except KeyError as e:
                        raise InvalidDeviceError("device name", device) from e
                except KeyError as e:
                    raise InvalidDeviceError("iOS Version", iOS_tag) from e
            elif udid_or_device:
                # Just a device name
                device = udid_or_device

                # Search iOS versions, looking for most recent version first.
                # The iOS tag will be something like "iOS 15.4";
                # Drop the prefix (if it exists), convert into the tuple (15, 4),
                # and sort numerically.
                for iOS_tag, devices in sorted(
                    simulators.items(),
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

                        return udid, iOS_version, device
                    except KeyError:
                        # UDID doesn't exist in this iOS version; try another.
                        pass
                raise InvalidDeviceError("device name", device) from e

        if len(simulators) == 0:
            raise BriefcaseCommandError("No iOS simulators available.")
        elif len(simulators) == 1:
            iOS_tag = list(simulators.keys())[0]
        else:
            iOS_tag = self.console.selection_question(
                intro="Select iOS version:",
                description="iOS Version",
                options=simulators.keys(),
            )

        devices = simulators[iOS_tag]

        if len(devices) == 0:
            raise BriefcaseCommandError(f"No simulators available for {iOS_tag}.")
        elif len(devices) == 1:
            udid = list(devices.keys())[0]
        else:
            udid = self.console.selection_question(
                intro="Select simulator device to use:",
                description="Simulator",
                options=devices,
            )

        device = devices[udid]

        self.console.info(
            f"""
In the future, you could specify this device by running:

    $ briefcase {self.command} iOS -d "{device}::{iOS_tag}"

or:

    $ briefcase {self.command} iOS -d {udid}
"""
        )

        # iOS_tag will be of the form "iOS 15.5"
        # Drop the "iOS" prefix when reporting the version.
        iOS_version = iOS_tag.split(" ", 1)[-1]

        return udid, iOS_version, device


class iOSXcodeCreateCommand(iOSXcodePassiveMixin, CreateCommand):
    description = "Create and populate a iOS Xcode project."

    def permissions_context(self, app: AppConfig, x_permissions: dict[str, str]):
        """Additional template context for permissions.

        :param app: The config object for the app
        :param x_permissions: The dictionary of known cross-platform permission
            definitions.
        :returns: The template context describing permissions for the app.
        """
        # The collection of info.plist entries
        info = {}

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

    def _extra_pip_args(self, app: AppConfig):
        """Any additional arguments that must be passed to pip when installing packages.

        :param app: The app configuration
        :returns: A list of additional arguments
        """
        return super()._extra_pip_args(app) + [
            "--only-binary=:all:",
            "--extra-index-url",
            "https://pypi.anaconda.org/beeware/simple",
        ]

    def _install_app_requirements(
        self,
        app: AppConfig,
        requires: list[str],
        app_packages_path: Path,
        **kwargs,
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
            )
        except FileNotFoundError:
            # If a plist file couldn't be found, it's an old-style support package;
            # Determine the min iOS version from the VERSIONS file in the support package.
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

        ios_min_tag = ios_min_version.replace(".", "_")

        # Feb 2025: The platform-site was moved into the xcframework as
        # `platform-config`. Look for the new location; fall back to the old location.
        device_platform_site = (
            self.support_path(app)
            / "Python.xcframework/ios-arm64/platform-config/arm64-iphoneos"
        )
        simulator_platform_site = (
            self.support_path(app)
            / "Python.xcframework/ios-arm64_x86_64-simulator"
            / f"platform-config/{self.tools.host_arch}-iphonesimulator"
        )
        if not device_platform_site.exists():
            device_platform_site = (
                self.support_path(app) / "platform-site/iphoneos.arm64"
            )
            simulator_platform_site = (
                self.support_path(app)
                / f"platform-site/iphonesimulator.{self.tools.host_arch}"
            )

        # Perform the initial install pass targeting the "iphoneos" platform
        super()._install_app_requirements(
            app,
            requires=requires,
            app_packages_path=app_packages_path.parent / "app_packages.iphoneos",
            progress_message="Installing app requirements for iPhone device...",
            pip_args=[
                f"--platform=ios_{ios_min_tag}_arm64_iphoneos",
            ],
            pip_kwargs={
                "env": {
                    "PYTHONPATH": str(device_platform_site),
                    "PIP_REQUIRE_VIRTUALENV": None,
                }
            },
            install_hint=f"""

This may be because the `iphoneos` wheels that are available are not compatible
with a minimum iOS version of {ios_min_version}.
""",
        )

        # Perform a second install pass targeting the "iphonesimulator" platform for the
        # current architecture
        super()._install_app_requirements(
            app,
            requires=requires,
            app_packages_path=app_packages_path.parent / "app_packages.iphonesimulator",
            progress_message="Installing app requirements for iPhone simulator...",
            pip_args=[
                f"--platform=ios_{ios_min_tag}_{self.tools.host_arch}_iphonesimulator",
            ],
            pip_kwargs={
                "env": {
                    "PYTHONPATH": str(simulator_platform_site),
                    "PIP_REQUIRE_VIRTUALENV": None,
                },
            },
            install_hint=f"""

This may indicate that an `iphoneos` wheel could be found, but an
`iphonesimulator` wheel could not be found; or that the `iphonesimulator`
binary wheels that are available are not compatible with a minimum iOS
version of {ios_min_version}.
""",
        )


class iOSXcodeUpdateCommand(iOSXcodeCreateCommand, UpdateCommand):
    description = "Update an existing iOS Xcode project."


class iOSXcodeOpenCommand(iOSXcodePassiveMixin, OpenCommand):
    description = "Open an existing iOS Xcode project."


class iOSXcodeBuildCommand(iOSXcodePassiveMixin, BuildCommand):
    description = "Build an iOS Xcode project."

    def info_plist_path(self, app: AppConfig):
        """Obtain the path to the application's plist file.

        :param app: The config object for the app
        :return: The full path of the application's plist file.
        """
        return self.bundle_path(app) / self.path_index(app, "info_plist_path")

    def update_app_metadata(self, app: AppConfig):
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

    def build_app(self, app: AppConfig, **kwargs):
        """Build the Xcode project for the application.

        :param app: The application to build
        """
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
                        "-arch",
                        self.tools.host_arch,
                        "-sdk",
                        "iphonesimulator",
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External service APIs.
        # This is abstracted to enable testing without patching.
        self.get_device_state = get_device_state

    def run_app(
        self,
        app: AppConfig,
        *,
        passthrough: list[str],
        udid=None,
        **options,
    ) -> dict | None:
        """Start the application.

        :param app: The config object for the app
        :param passthrough: The list of arguments to pass to the app
        :param udid: The device UDID to target. If ``None``, the user will
            be asked to select a device at runtime.
        """
        try:
            udid, iOS_version, device = self.select_target_device(udid)
        except InputDisabled as e:
            raise BriefcaseCommandError(
                "Input has been disabled; can't select a device to target."
            ) from e

        if app.test_mode:
            label = "test suite"
        else:
            label = "app"

        self.console.info(
            f"Starting {label} on an {device} running iOS {iOS_version} (device UDID {udid})",
            prefix=app.app_name,
        )

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

        if not app.test_mode:
            # We now know the simulator is *running*, so we can open it.
            # We don't need to open the simulator to run the test suite.
            try:
                with self.console.wait_bar("Opening simulator..."):
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
                ["xcrun", "simctl", "uninstall", udid, app.bundle_identifier]
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
                ["xcrun", "simctl", "install", udid, self.binary_path(app)]
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
        #   extension module.
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
                f'senderImagePath ENDSWITH "/{app.formal_name}"'
                f' OR (processImagePath ENDSWITH "/{app.formal_name}"'
                ' AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                ' OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                ' OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"))',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )

        # Wait for the log stream start up
        time.sleep(0.25)

        try:
            self.console.info(f"Starting {label}...", prefix=app.app_name)
            with self.console.wait_bar(f"Launching {label}..."):
                output = self.tools.subprocess.check_output(
                    ["xcrun", "simctl", "launch", udid, app.bundle_identifier]
                    + passthrough
                )
                try:
                    app_pid = int(output.split(":")[1].strip())
                except (IndexError, ValueError) as e:
                    raise BriefcaseCommandError(
                        f"Unable to determine PID of {label} {app.app_name}."
                    ) from e

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


class iOSXcodePackageCommand(iOSXcodeMixin, PackageCommand):
    description = "Package an iOS app."


class iOSXcodePublishCommand(iOSXcodeMixin, PublishCommand):
    description = "Publish an iOS app."
    publication_channels = ["ios_appstore"]
    default_publication_channel = "ios_appstore"


# Declare the briefcase command bindings
create = iOSXcodeCreateCommand
update = iOSXcodeUpdateCommand
open = iOSXcodeOpenCommand
build = iOSXcodeBuildCommand
run = iOSXcodeRunCommand
package = iOSXcodePackageCommand
publish = iOSXcodePublishCommand
