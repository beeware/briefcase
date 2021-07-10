import subprocess
import time
from uuid import UUID

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.config import BaseConfig
from briefcase.console import InputDisabled, select_option
from briefcase.exceptions import BriefcaseCommandError, InvalidDeviceError
from briefcase.integrations.xcode import (
    DeviceState,
    get_device_state,
    get_simulators
)
from briefcase.platforms.iOS import iOSMixin


class iOSXcodePassiveMixin(iOSMixin):
    output_format = 'Xcode'

    @property
    def packaging_formats(self):
        return ['ipa']

    @property
    def default_packaging_format(self):
        return 'ipa'

    def binary_path(self, app):
        return (
            self.bundle_path(app) / 'build' / 'Debug-iphonesimulator'
            / '{app.formal_name}.app'.format(app=app)
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
            '-d',
            '--device',
            dest='udid',
            help='The device to target; either a UDID, '
                 'a device name ("iPhone 11"), '
                 'or a device name and OS version ("iPhone 11::iOS 13.3")',
            required=False,
        )

    def select_target_device(self, udid_or_device=None):
        """
        Select the target device to use for iOS builds.

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
        simulators = self.get_simulators(self, 'iOS')

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
            raise InvalidDeviceError('device UDID', udid)

        except (ValueError, TypeError):
            # Provided value wasn't a UDID.
            # It must be a device or device+version
            if udid_or_device and '::' in udid_or_device:
                # A device name::version.
                device, iOS_version = udid_or_device.split('::')
                try:
                    devices = simulators[iOS_version]
                    try:
                        # Do a reverse lookup for UDID, based on a
                        # case-insensitive name lookup.
                        udid = {
                            name.lower(): udid
                            for udid, name in devices.items()
                        }[device.lower()]

                        # Found a match;
                        # normalize back to the official name and return.
                        device = devices[udid]
                        return udid, iOS_version, device
                    except KeyError:
                        raise InvalidDeviceError('device name', device)
                except KeyError:
                    raise InvalidDeviceError('iOS Version', iOS_version)
            elif udid_or_device:
                # Just a device name
                device = udid_or_device

                # Search iOS versions, looking for most recent version first.
                for iOS_version, devices in sorted(
                    simulators.items(),
                    key=lambda item: tuple(int(v) for v in item[0].split('.')),
                    reverse=True
                ):
                    try:
                        udid = {
                            name.lower(): udid
                            for udid, name in devices.items()
                        }[device.lower()]

                        # Found a match;
                        # normalize back to the official name and return.
                        device = devices[udid]
                        return udid, iOS_version, device
                    except KeyError:
                        # UDID doesn't exist in this iOS version; try another.
                        pass
                raise InvalidDeviceError('device name', device)

        if len(simulators) == 0:
            raise BriefcaseCommandError(
                "No iOS simulators available."
            )
        elif len(simulators) == 1:
            iOS_version = list(simulators.keys())[0]
        else:
            if self.input.enabled:
                print()
                print("Select iOS version:")
                print()
            iOS_version = select_option({
                version: version
                for version in simulators.keys()
            }, input=self.input)

        devices = simulators[iOS_version]

        if len(devices) == 0:
            raise BriefcaseCommandError(
                "No simulators available for iOS {iOS_version}.".format(
                    iOS_version=iOS_version
                )
            )
        elif len(devices) == 1:
            udid = list(devices.keys())[0]
        else:
            if self.input.enabled:
                print()
                print("Select simulator device:")
                print()
            udid = select_option(devices, input=self.input)

        device = devices[udid]

        print("In future, you could specify this device by running:")
        print()
        print('    briefcase {self.command} iOS -d "{device}::{iOS_version}"'.format(
            self=self,
            device=device,
            iOS_version=iOS_version
        ))
        print()
        print('or:')
        print()
        print("    briefcase {self.command} iOS -d {udid}".format(self=self, udid=udid))
        return udid, iOS_version, device


class iOSXcodeCreateCommand(iOSXcodePassiveMixin, CreateCommand):
    description = "Create and populate a iOS Xcode project."


class iOSXcodeUpdateCommand(iOSXcodePassiveMixin, UpdateCommand):
    description = "Update an existing iOS Xcode project."


class iOSXcodeBuildCommand(iOSXcodeMixin, BuildCommand):
    description = "Build an iOS Xcode project."

    def build_app(self, app: BaseConfig, udid=None, **kwargs):
        """
        Build the Xcode project for the application.

        :param app: The application to build
        :param udid: The device UDID to target. If ``None``, the user will
            be asked to select a device at runtime.
        """
        try:
            udid, iOS_version, device = self.select_target_device(udid)
        except InputDisabled:
            raise BriefcaseCommandError(
                "Input has been disabled; can't select a device to target."
            )

        print()
        print("Targeting an {device} running iOS {iOS_version} (device UDID {udid})".format(
            device=device,
            iOS_version=iOS_version,
            udid=udid,
        ))

        print()
        print('[{app.app_name}] Building XCode project...'.format(
            app=app
        ))

        # build_settings = [
        #     ('AD_HOC_CODE_SIGNING_ALLOWED', 'YES'),
        #     ('CODE_SIGN_IDENTITY', '-'),
        #     ('VALID_ARCHS', '"i386 x86_64"'),
        #     ('ARCHS', 'x86_64'),
        #     ('ONLY_ACTIVE_ARCHS', 'NO')
        # ]
        # build_settings_str = ['{}={}'.format(*x) for x in build_settings]

        try:
            print()
            self.subprocess.run(
                [
                    'xcodebuild',  # ' '.join(build_settings_str),
                    '-project', self.bundle_path(app) / '{app.formal_name}.xcodeproj'.format(app=app),
                    '-destination',
                    'platform="iOS Simulator,name={device},OS={iOS_version}"'.format(
                        device=device,
                        iOS_version=iOS_version,
                    ),
                    '-quiet',
                    '-configuration', 'Debug',
                    '-arch', 'x86_64',
                    '-sdk', 'iphonesimulator',
                    'build'
                ],
                check=True,
            )
            print('Build succeeded.')
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Unable to build app {app.app_name}.".format(app=app)
            )

        # Preserve the device selection as state.
        return {
            'udid': udid
        }


class iOSXcodeRunCommand(iOSXcodeMixin, RunCommand):
    description = "Run an iOS Xcode project."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External service APIs.
        # These are abstracted to enable testing without patching.
        self.get_device_state = get_device_state
        self.sleep = time.sleep

    def run_app(self, app: BaseConfig, udid=None, **kwargs):
        """
        Start the application.

        :param app: The config object for the app
        :param udid: The device UDID to target. If ``None``, the user will
            be asked to select a device at runtime.
        :param base_path: The path to the project directory.
        """
        try:
            udid, iOS_version, device = self.select_target_device(udid)
        except InputDisabled:
            raise BriefcaseCommandError(
                "Input has been disabled; can't select a device to target."
            )

        print()
        print(
            "[{app.app_name}] Starting app on an {device} running "
            "iOS {iOS_version} (device UDID {udid})".format(
                app=app,
                device=device,
                iOS_version=iOS_version,
                udid=udid,
            )
        )

        # The simulator needs to be booted before being started.
        # If it's shut down, we can boot it again; but if it's currently
        # shutting down, we need to wait for it to shut down before restarting.
        device_state = self.get_device_state(self, udid)
        if device_state not in {DeviceState.SHUTDOWN, DeviceState.BOOTED}:
            print('Waiting for simulator...', flush=True, end='')
            while device_state not in {DeviceState.SHUTDOWN, DeviceState.BOOTED}:
                self.sleep(2)
                print('.', flush=True, end='')
                device_state = self.get_device_state(self, udid)

        # We now know the simulator is either shut down or booted;
        # if it's shut down, start it again.
        if device_state == DeviceState.SHUTDOWN:
            try:
                print("Booting {device} simulator running iOS {iOS_version}...".format(
                        device=device,
                        iOS_version=iOS_version,
                    )
                )
                self.subprocess.run(
                    ['xcrun', 'simctl', 'boot', udid],
                    check=True
                )
            except subprocess.CalledProcessError:
                raise BriefcaseCommandError(
                    "Unable to boot {device} simulator running iOS {iOS_version}".format(
                        device=device,
                        iOS_version=iOS_version,
                    )
                )

        # We now know the simulator is *running*, so we can open it.
        try:
            print("Opening {device} simulator running iOS {iOS_version}...".format(
                    device=device,
                    iOS_version=iOS_version,
                )
            )
            self.subprocess.run(
                ['open', '-a', 'Simulator', '--args', '-CurrentDeviceUDID', udid],
                check=True
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Unable to open {device} simulator running iOS {iOS_version}".format(
                    device=device,
                    iOS_version=iOS_version,
                )
            )

        # Try to uninstall the app first. If the app hasn't been installed
        # before, this will still succeed.
        app_identifier = '.'.join([app.bundle, app.app_name])
        print('[{app.app_name}] Uninstalling old app version...'.format(
            app=app
        ))
        try:
            self.subprocess.run(
                ['xcrun', 'simctl', 'uninstall', udid, app_identifier],
                check=True
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Unable to uninstall old version of app {app.app_name}.".format(
                    app=app
                )
            )

        # Install the app.
        print('[{app.app_name}] Installing new app version...'.format(
            app=app
        ))
        try:
            self.subprocess.run(
                ['xcrun', 'simctl', 'install', udid, self.binary_path(app)],
                check=True
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Unable to install new version of app {app.app_name}.".format(
                    app=app
                )
            )

        print('[{app.app_name}] Starting app...'.format(
            app=app
        ))
        try:
            self.subprocess.run(
                ['xcrun', 'simctl', 'launch', udid, app_identifier],
                check=True
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Unable to launch app {app.app_name}.".format(
                    app=app
                )
            )

        # Start streaming logs for the app.
        try:
            print()
            print("[{app.app_name}] Following simulator log output (type CTRL-C to stop log)...".format(app=app))
            print("=" * 75)
            self.subprocess.run(
                [
                    "xcrun", "simctl", "spawn", udid,
                    "log", "stream",
                    "--style", "compact",
                    "--predicate", 'senderImagePath ENDSWITH "/{app.formal_name}"'.format(app=app)
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Unable to start log stream for app {app.app_name}.".format(app=app)
            )

        # Preserve the device selection as state.
        return {
            'udid': udid
        }


class iOSXcodePackageCommand(iOSXcodeMixin, PackageCommand):
    description = "Package an iOS app."


class iOSXcodePublishCommand(iOSXcodeMixin, PublishCommand):
    description = "Publish an iOS app."
    publication_channels = ['ios_appstore']
    default_publication_channel = 'ios_appstore'


# Declare the briefcase command bindings
create = iOSXcodeCreateCommand  # noqa
update = iOSXcodeUpdateCommand  # noqa
build = iOSXcodeBuildCommand  # noqa
run = iOSXcodeRunCommand  # noqa
package = iOSXcodePackageCommand  # noqa
publish = iOSXcodePublishCommand  # noqa
