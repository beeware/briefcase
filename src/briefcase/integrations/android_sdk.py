import re
import shutil
import subprocess
from pathlib import Path

from requests import exceptions as requests_exceptions

from briefcase.console import select_option
from briefcase.exceptions import (
    BriefcaseCommandError,
    InvalidDeviceError,
    NetworkFailure,
)

DEVICE_NOT_FOUND = re.compile(r"^error: device '[^']*' not found")


class AndroidDeviceNotAuthorized(BriefcaseCommandError):
    def __init__(self, device):
        self.device = device
        super().__init__(
            """
The device you have selected ({device}) has not had Developer Options
enabled. These options must be enabled before a device can be used as a
target for deployment. For details on how to enable Developer Options, visit:

    https://developer.android.com/studio/debug/dev-options#enable

Once you have enabled these options on your device, you will be able to select
this device as a deployment target.

""".format(
                device=device
            )
        )


def verify_android_sdk(command):
    """
    Verify an Android SDK is available.

    If the ANDROID_SDK_ROOT environment variable is set, that location will
    be checked for a valid SDK.

    If the location provided doesn't contain an SDK, or no location is provided,
    an SDK is downloaded.

    :param command: The command making the verification request.
    :returns: An AndroidSDK instance, bound to command.
    """
    sdk_root = command.os.environ.get("ANDROID_SDK_ROOT")
    if sdk_root:
        sdk = AndroidSDK(command=command, root_path=Path(sdk_root))

        if sdk.exists():
            # Ensure licenses have been accepted
            sdk.verify_license()
            return sdk
        else:
            print(
                """
*************************************************************************
** WARNING: ANDROID_SDK_ROOT does not point to an Android SDK          **
*************************************************************************

    The location pointed to by the ANDROID_SDK_ROOT environment variable:

     {sdk_root}

    doesn't appear to contain an Android SDK.

    Briefcase will use its own SDK instance.

*************************************************************************

""".format(
                    sdk_root=sdk_root
                )
            )

    # Build an SDK wrapper for the Briefcase SDK instance.
    sdk = AndroidSDK(
        command=command, root_path=command.dot_briefcase_path / "tools" / "android_sdk"
    )

    if sdk.exists():
        # Ensure licenses have been accepted
        sdk.verify_license()
        return sdk

    print("Setting up Android SDK...")
    try:
        sdk_zip_path = command.download_url(
            url=sdk.sdk_url, download_path=command.dot_briefcase_path / "tools",
        )
    except requests_exceptions.ConnectionError:
        raise NetworkFailure("download Android SDK")
    try:
        command.shutil.unpack_archive(str(sdk_zip_path), extract_dir=str(sdk.root_path))
    except (shutil.ReadError, EOFError):
        raise BriefcaseCommandError(
            """\
Unable to unpack Android SDK ZIP file. The download may have been interrupted
or corrupted.

Delete {sdk_zip_path} and run briefcase again.""".format(
                sdk_zip_path=sdk_zip_path
            )
        )

    # Zip file no longer needed once unpacked.
    sdk_zip_path.unlink()

    # Python zip unpacking ignores permission metadata.
    # On non-Windows, we manually fix permissions.
    if command.host_os != "Windows":
        for binpath in (sdk.root_path / "tools" / "bin").glob("*"):
            if not command.os.access(str(binpath), command.os.X_OK):
                binpath.chmod(0o755)

    # Licences must be accepted.
    sdk.verify_license()

    return sdk


class AndroidSDK:
    def __init__(self, command, root_path):
        self.command = command
        self.root_path = root_path

    @property
    def sdkmanager_path(self):
        sdkmanager = (
            "sdkmanager.bat" if self.command.host_os == "Windows" else "sdkmanager"
        )
        return self.root_path / "tools" / "bin" / sdkmanager

    @property
    def avdmanager_path(self):
        avdmanager = (
            "avdmanager.bat" if self.command.host_os == "Windows" else "avdmanager"
        )
        return self.root_path / "tools" / "bin" / avdmanager

    @property
    def emulator_path(self):
        emulator = "emulator.bat" if self.command.host_os == "Windows" else "emulator"
        return self.root_path / "tools" / "bin" / emulator

    @property
    def env(self):
        return {
            **self.command.os.environ,
            "ANDROID_SDK_ROOT": str(self.root_path),
            "JAVA_HOME": str(self.command.java_home_path),
        }

    @property
    def sdk_url(self):
        """The Android SDK URL appropriate to the current operating system."""
        # The URLs described by the pattern below have existed since
        # approximately 2017, and the code they download has a built-in
        # updater. I hope they will work for many years.
        return "https://dl.google.com/android/repository/" + (
            "sdk-tools-{os}-4333796.zip".format(os=self.command.host_os.lower())
        )

    def exists(self):
        """Confirm that the SDK actually exists.

        Look for the sdkmanager; and, if necessary, confirm that it is
        executable.
        """
        return self.sdkmanager_path.exists() and (
            self.command.host_os == "Windows"
            or self.command.os.access(str(self.sdkmanager_path), self.command.os.X_OK)
        )

    def adb(self, device):
        """Obtain an ADB instance for managing a specific device.

        :param device: The device ID to manage.
        """
        return ADB(self, device=device)

    def verify_license(self):
        """Verify that all necessary licenses have been accepted.

        If they haven't, prompt the user to do so.

        Raises an error if licenses are not.
        """
        license_path = self.root_path / "licenses" / "android-sdk-license"
        if license_path.exists():
            return

        print(
            "\n"
            + """\
    The Android tools provided by Google have license terms that you must accept
    before you may use those tools.
    """
        )
        try:
            # Using subprocess.run() with no I/O redirection so the user sees
            # the full output and can send input.
            self.command.subprocess.run(
                [str(self.sdkmanager_path), "--licenses"], env=self.env, check=True,
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                """\
    Error while reviewing Android SDK licenses. Please run this command and examine
    its output for errors.

    $ {sdkmanager} --licenses""".format(
                    sdkmanager=self.root_path / "tools" / "bin" / "sdkmanager"
                )
            )

        if not license_path.exists():
            raise BriefcaseCommandError(
                """\
    You did not accept the Android SDK licenses. Please re-run the briefcase command
    and accept the Android SDK license when prompted. You may need an Internet
    connection."""
            )

    def verify_emulator(self):
        """Verify that Android emulator has been installed.

        Raises an error if the emulator can't be installed.
        """
        if (self.root_path / "emulator").exists():
            return

        print("Downloading the Android emulator and system image...")
        try:
            # Using `check_output` and `stderr=STDOUT` so we buffer output,
            # displaying it only if an exception occurs.
            self.command.subprocess.run(
                [
                    str(self.sdkmanager_path),
                    "platforms;android-28",
                    "system-images;android-28;default;x86",
                    "emulator",
                    "platform-tools",
                ],
                env=self.env,
                check=True,
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Error while installing Android emulator and system image."
            )

    def emulators(self):
        """Find the list of emulators that are available

        """
        try:
            # Capture `stderr` so that if the process exits with failure, the
            # stderr data is in `e.output`.
            output = self.command.subprocess.check_output(
                [str(self.root_path / "emulator" / "emulator"), "-list-avds"],
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            ).strip()

            # AVD names are returned one per line.
            if len(output) == 0:
                return []
            return output.split("\n")
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError("Unable to obtain Android emulator list")

    def devices(self):
        """Find the devices that are attached and available to ADB

        """
        try:
            # Capture `stderr` so that if the process exits with failure, the
            # stderr data is in `e.output`.
            output = self.command.subprocess.check_output(
                [str(self.root_path / "platform-tools" / "adb"), "devices", "-l"],
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            ).strip()

            # Process the output of `adb devices -l`.
            # The first line is header information.
            # Each subsequent line is a single device descriptor.
            devices = {}
            for line in output.split("\n")[1:]:
                parts = re.sub(r"\s+", " ", line).split(" ")

                details = {}
                for part in parts[2:]:
                    key, value = part.split(":")
                    details[key] = value

                if parts[1] == "device":
                    name = details["device"]
                    authorized = True
                else:
                    name = "Unknown device (not authorized for development)"
                    authorized = False

                devices[parts[0]] = {
                    "name": name,
                    "authorized": authorized,
                }

            return devices
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError("Unable to obtain Android device list")

    def select_target_device(self, device_or_avd):
        """
        Select a device to be the target for actions

        Interrogates the system to get the list of available devices

        If the user has specified a device at the command line, that device
        will be validated, and then automatically selected

        :param device_or_avd: The device or AVD to target. Can be a physical
            device id (a hex string), an emulator id ("emulator-5554"), or
            an emulator AVD name ("@robotfriend"). If ``None``, the user will
            be asked to select a device from the list available.
        :returns: A tuple containing ``(device, name, avd)``. ``avd``
            will only be provided if an emulator with that AVD is not currently
            running. If ``device`` is null, a new emulator should be created.
        """
        # Get the list of attached devices (includes running emulators)
        running_devices = self.devices()

        # Choices is an ordered list of options that can be shown to the user.
        # Each device should appear only once, and be keyed by AVD only if
        # a device ID isn't available.
        choices = []
        # Device choices is the full lookup list. Devices can be looked up
        # by any valid key - ID *or* AVD.
        device_choices = {}

        # Iterate over all the running devices.
        # If the device has an AVD, use ADB to get the emulator AVD name.
        # If it is a physical device, use the device name.
        # Keep a log of all running AVDs
        running_avds = {}
        for d, details in sorted(running_devices.items(), key=lambda d: d[1]["name"]):
            name = details["name"]
            avd = self.adb(d).avd_name()
            if avd:
                # It's a running emulator
                running_avds[avd] = d
                full_name = "@{avd} (running {name} emulator)".format(
                    avd=avd, name=name,
                )
                choices.append((d, full_name))

                # Save the AVD as a device detail.
                details["avd"] = avd

                # Device can be looked up by device ID or AVD
                device_choices[d] = full_name
                device_choices["@" + avd] = full_name
            else:
                # It's a physical device (might be disabled)
                choices.append((d, name))
                device_choices[d] = name

        # Add any non-running emulator AVDs to the list of candidate devices
        for avd in self.emulators():
            if avd not in running_avds:
                name = "@{avd} (emulator)".format(avd=avd)
                choices.append(("@" + avd, name))
                device_choices["@" + avd] = name

        # If a device or AVD has been provided, check it against the available
        # device list.
        if device_or_avd:
            try:
                name = device_choices[device_or_avd]

                if device_or_avd.startswith("@"):
                    # specifier is an AVD
                    try:
                        avd = device_or_avd[1:]
                        device = running_avds[avd]
                    except KeyError:
                        # device_or_avd isn't in the list of running avds;
                        # it must be a non-running emulator.
                        return None, name, avd
                else:
                    # Specifier is a direct device ID
                    avd = None
                    device = device_or_avd

                details = running_devices[device]
                avd = details.get("avd")
                if details["authorized"]:
                    # An authorized, running device (emulator or physical)
                    return device, name, avd
                else:
                    # An unauthorized physical device
                    raise AndroidDeviceNotAuthorized(device)

            except KeyError:
                # Provided device_or_id isn't a valid device identifier.
                if device_or_avd.startswith("@"):
                    id_type = "emulator AVD"
                else:
                    id_type = "device ID"
                raise InvalidDeviceError(id_type, device_or_avd)

        # We weren't given a device/AVD; we have to select from the list.
        # If we're selecting from a list, there's always one last choice
        choices.append((None, "Create a new Android emulator"))

        # Show the choices to the user.
        print()
        print("Select device:")
        print()
        choice = select_option(choices, input=self.command.input)

        # Proces the user's choice
        if choice is None:
            # Create a new emulator. No device ID or AVD.
            device = None
            avd = None
            name = None
        elif choice.startswith("@"):
            # A non-running emulator. We have an AVD, but no device ID.
            device = None
            name = device_choices[choice]
            avd = choice[1:]
        else:
            # Either a running emulator, or a physical device. Regardless,
            # we need to check if the device is developer enabled
            try:
                details = running_devices[choice]
                if not details["authorized"]:
                    # An unauthorized physical device
                    raise AndroidDeviceNotAuthorized(choice)

                # Return the device ID and name.
                device = choice
                name = device_choices[choice]
                avd = details.get("avd")
            except KeyError:
                raise InvalidDeviceError("device ID", choice)

        if avd:
            print()
            print("In future, you could specify this device by running:")
            print()
            print("    briefcase run android -d @{avd}".format(avd=avd))
        elif device:
            print()
            print("In future, you could specify this device by running:")
            print()
            print("    briefcase run android -d {device}".format(device=device))

        return device, name, avd

    def create_emulator(self):
        """Create a new Android emulator.

        """
        print()
        name = self.command.input("Emulator name: ")

        raise BriefcaseCommandError(
            """
You can create an emulator by running:

    $ {sdkmanager_path} "platforms;android-28" \
"system-images;android-28;default;x86" "emulator" "platform-tools"

    $ {avdmanager_path} --verbose create avd \
--name {name} --abi x86 \
--package 'system-images;android-28;default;x86' --device pixel

    $ echo 'disk.dataPartition.size=4096M' >> $HOME/.android/avd/{name}.avd/config.ini

""".format(
                sdkmanager_path=self.sdkmanager_path,
                avdmanager_path=self.avdmanager_path,
                name=name,
            )
        )

    def start_emulator(self, avd):
        """Start an existing Android emulator.

        Returns when the emulator is booted and ready to accept apps.

        :param avd: The AVD of the device.
        """
        if avd in set(self.emulators()):
            raise BriefcaseCommandError(
                """
You can start the emulator by running:

    $ {emulator_path} -avd {avd} &

""".format(
                    emulator_path=self.emulator_path, avd=avd
                )
            )
        else:
            raise InvalidDeviceError("emulator AVD", avd)


class ADB:
    def __init__(self, android_sdk, device):
        """
        An API integration for the Android Debug Bridge (ADB).

        :param android_sdk: The Android SDK providing ADB.
        :param device: The ID of the device to target (in a format usable by
            `adb -s`)
        """
        self.android_sdk = android_sdk
        self.command = android_sdk.command
        self.device = device

    def avd_name(self):
        """Get the AVD name for the device.

        :returns: The AVD name for the device; or ``None`` if the device isn't
            an emulator
        """
        try:
            output = self.run("emu", "avd", "name")
            return output.split("\n")[0]
        except subprocess.CalledProcessError as e:
            # Status code 1 is a normal "it's not an emulator" error response
            if e.returncode == 1:
                return None
            else:
                raise BriefcaseCommandError(
                    "Unable to interrogate AVD name of device {device}".format(
                        device=self.device
                    )
                )

    def run(self, *arguments):
        """
        Run a command on a device using Android debug bridge, `adb`. The device
        name is mandatory to ensure clarity in the case of multiple attached
        devices.

        :param arguments: List of strings to pass to `adb` as arguments.

        Returns bytes of `adb` output on success; raises an exception on failure.
        """
        # The ADB integration operates on the basis of running commands before
        # checking that they are valid, then parsing output to notice errors.
        # This keeps performance good in the success case.
        try:
            # Capture `stderr` so that if the process exits with failure, the
            # stderr data is in `e.output`.
            return self.command.subprocess.check_output(
                [
                    str(self.android_sdk.root_path / "platform-tools" / "adb"),
                    "-s",
                    self.device,
                ]
                + list(arguments),
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            if any((DEVICE_NOT_FOUND.match(line) for line in e.output.split("\n"))):
                raise InvalidDeviceError("device id", self.device)
            raise

    def install_apk(self, apk_path):
        """
        Install an APK file on an Android device.

        :param apk_path: The path of the Android APK file to install.

        Returns `None` on success; raises an exception on failure.
        """
        try:
            self.run("install", str(apk_path))
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Unable to install APK {apk_path} on {device}".format(
                    apk_path=apk_path, device=self.device,
                )
            )

    def force_stop_app(self, package):
        """
        Force-stop an app, specified as a package name.

        :param package: The name of the Android package, e.g., com.username.myapp.

        Returns `None` on success; raises an exception on failure.
        """
        # In my testing, `force-stop` exits with status code 0 (success) so long
        # as you pass a package name, even if the package does not exist, or the
        # package is not running.
        try:
            self.run("shell", "am", "force-stop", package)
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Unable to force stop app {package} on {device}".format(
                    package=package, device=self.device,
                )
            )

    def start_app(self, package, activity):
        """
        Start an app, specified as a package name & activity name.

        :param package: The name of the Android package, e.g., com.username.myapp.
        :param activity: The activity of the APK to start.

        Returns `None` on success; raises an exception on failure.

        If you have an APK file, and you are not sure of the package or activity
        name, you can find it using `aapt dump badging filename.apk` and looking
        for "package" and "launchable-activity" in the output.
        """
        try:
            # `adb shell am start` always exits with status zero. We look for error
            # messages in the output.
            output = self.run(
                "shell",
                "am",
                "start",
                "{package}/{activity}".format(package=package, activity=activity),
                "-a",
                "android.intent.action.MAIN",
                "-c",
                "android.intent.category.LAUNCHER",
            )

            if any(
                (
                    line.startswith("Error: Activity class ")
                    and line.endswith("does not exist.")
                    for line in output.split("\n")
                )
            ):
                raise BriefcaseCommandError(
                    """\
    Activity class not found while starting app.

    `adb` output:

    {output}""".format(
                        output=output
                    )
                )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Unable to start {package}/{activity} on {device}".format(
                    package=package, activity=activity, device=self.device,
                )
            )
