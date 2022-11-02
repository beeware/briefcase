import subprocess
import time
from uuid import UUID

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    TestCommand,
    UpdateCommand,
)
from briefcase.config import BaseConfig
from briefcase.console import InputDisabled, select_option
from briefcase.exceptions import (
    BriefcaseCommandError,
    InvalidDeviceError,
    TestSuiteFailure,
)
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

    def project_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.xcodeproj"

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
            self.input.prompt()
            self.input.prompt("Select iOS version:")
            self.input.prompt()
            iOS_tag = select_option(
                {tag: tag for tag in simulators.keys()}, input=self.input
            )

        devices = simulators[iOS_tag]

        if len(devices) == 0:
            raise BriefcaseCommandError(f"No simulators available for {iOS_tag}.")
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

    def _extra_pip_args(self, app: BaseConfig):
        """Any additional arguments that must be passed to pip when installing
        packages.

        :param app: The app configuration
        :returns: A list of additional arguments
        """
        return [
            "--prefer-binary",
            "--extra-index-url",
            "https://pypi.anaconda.org/beeware/simple",
        ]


class iOSXcodeUpdateCommand(iOSXcodeCreateCommand, UpdateCommand):
    description = "Update an existing iOS Xcode project."


class iOSXcodeOpenCommand(iOSXcodePassiveMixin, OpenCommand):
    description = "Open an existing iOS Xcode project."


class iOSXcodeBuildCommand(iOSXcodePassiveMixin, BuildCommand):
    description = "Build an iOS Xcode project."

    def build_app(self, app: BaseConfig, **kwargs):
        """Build the Xcode project for the application.

        :param app: The application to build
        """
        self.logger.info("Building XCode project...", prefix=app.app_name)
        with self.input.wait_bar("Building..."):
            try:
                self.tools.subprocess.run(
                    [
                        "xcodebuild",
                        "build",
                        "-project",
                        self.project_path(app),
                        "-destination",
                        'platform="iOS Simulator"',
                        "-configuration",
                        "Debug",
                        "-arch",
                        self.tools.host_arch,
                        "-sdk",
                        "iphonesimulator",
                        "-quiet",
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to build app {app.app_name}."
                ) from e


class iOSXcodeTestCommand(iOSXcodeMixin, TestCommand):
    description = "Test an iOS Xcode project."

    def test_app(self, app: BaseConfig, udid=None, **kwargs):
        """Test the Xcode project for the application.

        :param app: The application to test
        :param udid: The device UDID to target. If ``None``, the user will
            be asked to select a device at runtime.
        """
        try:
            udid, iOS_version, device = self.select_target_device(udid)
        except InputDisabled as e:
            raise BriefcaseCommandError(
                "Input has been disabled; can't select a device to target."
            ) from e

        self.logger.info(
            f"Targeting an {device} running iOS {iOS_version} (device UDID {udid})",
            prefix=app.app_name,
        )

        """Test the Xcode project for the application.

        :param app: The application to test
        """
        self.logger.info("Installing Test code...", prefix=app.app_name)
        self.install_test_code(app=app)

        self.logger.info("Installing Test dependencies...", prefix=app.app_name)
        self.install_test_dependencies(app=app)

        self.logger.info("Building XCode Test project...", prefix=app.app_name)
        with self.input.wait_bar("Building..."):
            try:
                self.tools.subprocess.run(
                    [
                        "xcodebuild",
                        "build-for-testing",
                        "-project",
                        self.project_path(app),
                        "-scheme",
                        app.formal_name,
                        "-configuration",
                        "Debug",
                        "-destination",
                        f"platform=iOS Simulator,name={device},OS={iOS_version}",
                        "-quiet",
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to build test app {app.app_name}."
                ) from e

        # Start the logger
        try:
            self.logger.info("Starting logger...", prefix=app.app_name)
            log_popen = self.tools.subprocess.Popen(
                [
                    "log",
                    "stream",
                    "--style",
                    "compact",
                    "--predicate",
                    f'senderImagePath ENDSWITH "/{app.formal_name}"'
                    f'OR (processImagePath ENDSWITH "/{app.formal_name}"'
                    ' AND senderImagePath ENDSWITH "-iphonesimulator.so")',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            )

            # Wait for the log stream start up
            time.sleep(0.25)

            self.logger.info("Testing XCode project...", prefix=app.app_name)
            test_popen = self.tools.subprocess.Popen(
                [
                    "xcodebuild",
                    "test-without-building",
                    "-project",
                    self.project_path(app),
                    "-scheme",
                    app.formal_name,
                    "-configuration",
                    "Debug",
                    "-destination",
                    f"platform=iOS Simulator,name={device},OS={iOS_version}",
                    "-quiet",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            )
            # Wait for the test runner to start up
            time.sleep(0.25)

            # Start streaming logs for the test.
            self.logger.info("=" * 75)
            self.tools.subprocess.stream_output(
                "log stream", log_popen, stop_func=lambda: test_popen.poll() is not None
            )
            self.logger.info("=" * 75)

            if test_popen.returncode == 0:
                self.logger.info("Test suite passed!", prefix=app.app_name)
            else:
                self.logger.error("Test suite failed!", prefix=app.app_name)
                raise TestSuiteFailure()
        except KeyboardInterrupt:
            pass  # Catch CTRL-C to exit normally
        finally:
            self.tools.subprocess.cleanup("log stream", log_popen)
            try:
                self.tools.subprocess.cleanup("test runner", test_popen)
            except NameError:
                # Failure occurred before test_popen was created
                pass

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

        self.logger.info(
            f"Starting app on an {device} running iOS {iOS_version} (device UDID {udid})",
            prefix=app.app_name,
        )

        # The simulator needs to be booted before being started.
        # If it's shut down, we can boot it again; but if it's currently
        # shutting down, we need to wait for it to shut down before restarting.
        device_state = self.get_device_state(self.tools, udid)
        if device_state not in {DeviceState.SHUTDOWN, DeviceState.BOOTED}:
            with self.input.wait_bar("Waiting for simulator shutdown..."):
                while device_state not in {DeviceState.SHUTDOWN, DeviceState.BOOTED}:
                    self.sleep(2)
                    device_state = self.get_device_state(self.tools, udid)

        # We now know the simulator is either shut down or booted;
        # if it's shut down, start it again.
        if device_state == DeviceState.SHUTDOWN:
            try:
                with self.input.wait_bar("Booting simulator..."):
                    self.tools.subprocess.run(
                        ["xcrun", "simctl", "boot", udid],
                        check=True,
                    )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to boot {device} simulator running {iOS_version}"
                ) from e

        # We now know the simulator is *running*, so we can open it.
        try:
            with self.input.wait_bar("Opening simulator..."):
                self.tools.subprocess.run(
                    ["open", "-a", "Simulator", "--args", "-CurrentDeviceUDID", udid],
                    check=True,
                )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to open {device} simulator running {iOS_version}"
            ) from e

        # Try to uninstall the app first. If the app hasn't been installed
        # before, this will still succeed.
        app_identifier = ".".join([app.bundle, app.app_name])
        try:
            self.logger.info("Installing app...", prefix=app.app_name)
            with self.input.wait_bar("Uninstalling any existing app version..."):
                self.tools.subprocess.run(
                    ["xcrun", "simctl", "uninstall", udid, app_identifier],
                    check=True,
                )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to uninstall old version of app {app.app_name}."
            ) from e

        # Install the app.
        try:
            with self.input.wait_bar("Installing new app version..."):
                self.tools.subprocess.run(
                    ["xcrun", "simctl", "install", udid, self.binary_path(app)],
                    check=True,
                )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to install new version of app {app.app_name}."
            ) from e

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
                ' AND senderImagePath ENDSWITH "-iphonesimulator.so")',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )

        # Wait for the log stream start up
        self.sleep(0.25)

        try:
            self.logger.info("Starting app...", prefix=app.app_name)
            try:
                with self.input.wait_bar("Launching app..."):
                    self.tools.subprocess.run(
                        ["xcrun", "simctl", "launch", udid, app_identifier],
                        check=True,
                    )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to launch app {app.app_name}."
                ) from e

            # Start streaming logs for the app.
            self.logger.info(
                "Following simulator log output (type CTRL-C to stop log)...",
                prefix=app.app_name,
            )
            self.logger.info("=" * 75)
            self.tools.subprocess.stream_output("log stream", simulator_log_popen)
        except KeyboardInterrupt:
            pass  # catch CTRL-C to exit normally
        finally:
            self.tools.subprocess.cleanup("log stream", simulator_log_popen)

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
open = iOSXcodeOpenCommand  # noqa
build = iOSXcodeBuildCommand  # noqa
test = iOSXcodeTestCommand  # noqa
run = iOSXcodeRunCommand  # noqa
package = iOSXcodePackageCommand  # noqa
publish = iOSXcodePublishCommand  # noqa
