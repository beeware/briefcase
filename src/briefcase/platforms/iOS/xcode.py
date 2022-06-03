import subprocess
import time
from uuid import UUID

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import BaseConfig
from briefcase.console import InputDisabled, select_option
from briefcase.exceptions import BriefcaseCommandError, InvalidDeviceError
from briefcase.integrations.xcode import DeviceState, get_device_state, get_simulators
from briefcase.platforms.iOS import iOSMixin


class iOSXcodePassiveMixin(iOSMixin):
    output_format = "Xcode"

    @property
    def packaging_formats(self):
        return ["ipa"]

    @property
    def default_packaging_format(self):
        return "ipa"

    def binary_path(self, app):
        return (
            self.bundle_path(app)
            / "build"
            / "Debug-iphonesimulator"
            / f"{app.formal_name}.app"
        )

    def distribution_path(self, app, packaging_format):
        return self.binary_path(app)


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
        simulators = self.get_simulators(self, "iOS")

        try:
            # Try to convert to a UDID. If this succeeds, then the argument
            # is a UDID.
            udid = str(UUID(udid_or_device)).upper()
            # User has provided a UDID at the command line; look for it.
            for iOS_version, devices in simulators.items():
                try:
                    device = devices[udid]
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
                device, iOS_version = udid_or_device.split("::")
                try:
                    # Convert the simulator dict into a dict where
                    # the iOS versions are lower cased, then do a lookup
                    # on the lower case name provided by the user.
                    # However, also return the *unmodified* iOS version string
                    # so we can convert the user-provided iOS version into the
                    # "clean", official capitalization.
                    iOS_version, devices = {
                        clean_iOS_version.lower(): (clean_iOS_version, details)
                        for clean_iOS_version, details in simulators.items()
                    }[iOS_version.lower()]
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
                except KeyError as err:
                    raise InvalidDeviceError("iOS Version", iOS_version) from err
            elif udid_or_device:
                # Just a device name
                device = udid_or_device

                # Search iOS versions, looking for most recent version first.
                # The iOS version string will be something like "iOS 15.4";
                # Drop the prefix (if it exists), convert into the tuple (15, 4),
                # and sort numerically.
                for iOS_version, devices in sorted(
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
                        return udid, iOS_version, device
                    except KeyError:
                        # UDID doesn't exist in this iOS version; try another.
                        pass
                raise InvalidDeviceError("device name", device) from e

        if len(simulators) == 0:
            raise BriefcaseCommandError("No iOS simulators available.")
        elif len(simulators) == 1:
            iOS_version = list(simulators.keys())[0]
        else:
            self.input.prompt()
            self.input.prompt("Select iOS version:")
            self.input.prompt()
            iOS_version = select_option(
                {version: version for version in simulators.keys()}, input=self.input
            )

        devices = simulators[iOS_version]

        if len(devices) == 0:
            raise BriefcaseCommandError(f"No simulators available for {iOS_version}.")
        elif len(devices) == 1:
            udid = list(devices.keys())[0]
        else:
            self.input.prompt()
            self.input.prompt("Select simulator device:")
            self.input.prompt()
            udid = select_option(devices, input=self.input)

        device = devices[udid]

        self.logger.info(
            f"""
In the future, you could specify this device by running:

    briefcase {self.command} iOS -d "{device}::{iOS_version}"

or:

    briefcase {self.command} iOS -d {udid}
"""
        )
        return udid, iOS_version, device


class iOSXcodeCreateCommand(iOSXcodePassiveMixin, CreateCommand):
    description = "Create and populate a iOS Xcode project."


class iOSXcodeUpdateCommand(iOSXcodePassiveMixin, UpdateCommand):
    description = "Update an existing iOS Xcode project."


class iOSXcodeBuildCommand(iOSXcodeMixin, BuildCommand):
    description = "Build an iOS Xcode project."

    def build_app(self, app: BaseConfig, udid=None, **kwargs):
        """Build the Xcode project for the application.

        :param app: The application to build
        :param udid: The device UDID to target. If ``None``, the user will
            be asked to select a device at runtime.
        """
        try:
            udid, iOS_version, device = self.select_target_device(udid)
        except InputDisabled as e:
            raise BriefcaseCommandError(
                "Input has been disabled; can't select a device to target."
            ) from e

        self.logger.info()
        self.logger.info(
            f"Targeting an {device} running {iOS_version} (device UDID {udid})"
        )

        self.logger.info()
        self.logger.info("Building XCode project...", prefix=app.app_name)

        try:
            self.subprocess.run(
                [
                    "xcodebuild",
                    "-project",
                    self.bundle_path(app) / f"{app.formal_name}.xcodeproj",
                    "-destination",
                    f'platform="iOS Simulator,name={device},OS={iOS_version}"',
                    "-quiet",
                    "-configuration",
                    "Debug",
                    "-arch",
                    self.host_arch,
                    "-sdk",
                    "iphonesimulator",
                    "build",
                ],
                check=True,
            )
            self.logger.info("Build succeeded.")
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to build app {app.app_name}.") from e

        # Preserve the device selection as state.
        return {"udid": udid}


class iOSXcodeRunCommand(iOSXcodeMixin, RunCommand):
    description = "Run an iOS Xcode project."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External service APIs.
        # These are abstracted to enable testing without patching.
        self.get_device_state = get_device_state
        self.sleep = time.sleep

    def run_app(self, app: BaseConfig, udid=None, **kwargs):
        """Start the application.

        :param app: The config object for the app
        :param udid: The device UDID to target. If ``None``, the user will
            be asked to select a device at runtime.
        """
        try:
            udid, iOS_version, device = self.select_target_device(udid)
        except InputDisabled as e:
            raise BriefcaseCommandError(
                "Input has been disabled; can't select a device to target."
            ) from e

        self.logger.info()
        self.logger.info(
            f"Starting app on an {device} running {iOS_version} (device UDID {udid})",
            prefix=app.app_name,
        )
        self.logger.info()

        # The simulator needs to be booted before being started.
        # If it's shut down, we can boot it again; but if it's currently
        # shutting down, we need to wait for it to shut down before restarting.
        device_state = self.get_device_state(self, udid)
        if device_state not in {DeviceState.SHUTDOWN, DeviceState.BOOTED}:
            with self.input.wait_bar("Waiting for simulator shutdown..."):
                while device_state not in {DeviceState.SHUTDOWN, DeviceState.BOOTED}:
                    self.sleep(2)
                    device_state = self.get_device_state(self, udid)

        # We now know the simulator is either shut down or booted;
        # if it's shut down, start it again.
        if device_state == DeviceState.SHUTDOWN:
            try:
                with self.input.wait_bar("Booting simulator..."):
                    self.subprocess.run(
                        ["xcrun", "simctl", "boot", udid],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                    )
            except subprocess.CalledProcessError as e:
                self.logger.error()
                self.logger.error(e.stdout)
                raise BriefcaseCommandError(
                    f"Unable to boot {device} simulator running {iOS_version}"
                ) from e

        # We now know the simulator is *running*, so we can open it.
        try:
            with self.input.wait_bar("Opening simulator..."):
                self.subprocess.run(
                    ["open", "-a", "Simulator", "--args", "-CurrentDeviceUDID", udid],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
        except subprocess.CalledProcessError as e:
            self.logger.error()
            self.logger.error(e.stdout)
            raise BriefcaseCommandError(
                f"Unable to open {device} simulator running {iOS_version}"
            ) from e

        # Try to uninstall the app first. If the app hasn't been installed
        # before, this will still succeed.
        app_identifier = ".".join([app.bundle, app.app_name])
        try:
            with self.input.wait_bar("Uninstalling old app version..."):
                self.subprocess.run(
                    ["xcrun", "simctl", "uninstall", udid, app_identifier],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
        except subprocess.CalledProcessError as e:
            self.logger.error()
            self.logger.error(e.stdout)
            raise BriefcaseCommandError(
                f"Unable to uninstall old version of app {app.app_name}."
            ) from e

        # Install the app.
        try:
            with self.input.wait_bar("Installing new app version..."):
                self.subprocess.run(
                    ["xcrun", "simctl", "install", udid, self.binary_path(app)],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
        except subprocess.CalledProcessError as e:
            self.logger.error()
            self.logger.error(e.stdout)
            raise BriefcaseCommandError(
                f"Unable to install new version of app {app.app_name}."
            ) from e

        # Start log stream for the app.
        simulator_log_popen = self.subprocess.Popen(
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
                f'senderImagePath ENDSWITH "/{app.formal_name}"',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )

        # Wait for the log stream start up
        self.sleep(0.25)

        try:
            with self.input.wait_bar("Starting app..."):
                self.subprocess.run(
                    ["xcrun", "simctl", "launch", udid, app_identifier],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
        except subprocess.CalledProcessError as e:
            self.subprocess.cleanup("log stream", simulator_log_popen)
            self.logger.error()
            self.logger.error(e.stdout)
            raise BriefcaseCommandError(f"Unable to launch app {app.app_name}.") from e

        # Start streaming logs for the app.
        self.logger.info()
        self.logger.info(
            "Following simulator log output (type CTRL-C to stop log)...",
            prefix=app.app_name,
        )
        self.logger.info("=" * 75)
        self.subprocess.stream_output("log stream", simulator_log_popen)

        # Preserve the device selection as state.
        return {"udid": udid}


class iOSXcodePackageCommand(iOSXcodeMixin, PackageCommand):
    description = "Package an iOS app."


class iOSXcodePublishCommand(iOSXcodeMixin, PublishCommand):
    description = "Publish an iOS app."
    publication_channels = ["ios_appstore"]
    default_publication_channel = "ios_appstore"


# Declare the briefcase command bindings
create = iOSXcodeCreateCommand  # noqa
update = iOSXcodeUpdateCommand  # noqa
build = iOSXcodeBuildCommand  # noqa
run = iOSXcodeRunCommand  # noqa
package = iOSXcodePackageCommand  # noqa
publish = iOSXcodePublishCommand  # noqa
