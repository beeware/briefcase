import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from requests import exceptions as requests_exceptions

from briefcase.config import PEP508_NAME_RE
from briefcase.console import InputDisabled, select_option
from briefcase.exceptions import (
    BriefcaseCommandError,
    InvalidDeviceError,
    MissingToolError,
    NetworkFailure
)
from briefcase.integrations.java import JDK

DEVICE_NOT_FOUND = re.compile(r"^error: device '[^']*' not found")


class AndroidDeviceNotAuthorized(BriefcaseCommandError):
    def __init__(self, device):
        self.device = device
        super().__init__(
            """
The device you have selected ({device}) has not had developer options and
USB debugging enabled. These must be enabled before a device can be used  as a
target for deployment. For details on how to enable Developer Options, visit:

    https://developer.android.com/studio/debug/dev-options#enable

Once you have enabled these options on your device, you will be able to select
this device as a deployment target.

""".format(
                device=device
            )
        )


class AndroidSDK:
    name = 'android_sdk'
    full_name = 'Android SDK'

    def __init__(self, command, jdk, root_path):
        self.command = command
        self.dot_android_path = self.command.home_path / ".android"
        self.jdk = jdk
        self.root_path = root_path

        # A wrapper for testing purposes
        self.sleep = time.sleep

    @property
    def sdkmanager_path(self):
        sdkmanager = (
            "sdkmanager.bat" if self.command.host_os == "Windows" else "sdkmanager"
        )
        return self.root_path / "tools" / "bin" / sdkmanager

    @property
    def adb_path(self):
        adb = "adb.exe" if self.command.host_os == "Windows" else "adb"
        return self.root_path / "platform-tools" / adb

    @property
    def avdmanager_path(self):
        avdmanager = (
            "avdmanager.bat" if self.command.host_os == "Windows" else "avdmanager"
        )
        return self.root_path / "tools" / "bin" / avdmanager

    @property
    def emulator_path(self):
        emulator = "emulator.exe" if self.command.host_os == "Windows" else "emulator"
        return self.root_path / "emulator" / emulator

    @property
    def avd_path(self):
        return self.dot_android_path / "avd"

    @property
    def env(self):
        return {
            **self.command.os.environ,
            "ANDROID_SDK_ROOT": os.fsdecode(self.root_path),
            "JAVA_HOME": str(self.jdk.java_home),
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

    @classmethod
    def verify(cls, command, install=True, jdk=None):
        """
        Verify an Android SDK is available.

        If the ANDROID_SDK_ROOT environment variable is set, that location will
        be checked for a valid SDK.

        If the location provided doesn't contain an SDK, or no location is provided,
        an SDK is downloaded.

        :param command: The command making the verification request.
        :param install: Should the tool be installed if it is not found?
        :param jdk: The JDK instance to use.
        :returns: A valid Android SDK wrapper. If Android SDK is not
            available, and was not installed, raises MissingToolError.
        """
        if jdk is None:
            jdk = JDK.verify(command, install=install)

        sdk_root = command.os.environ.get("ANDROID_SDK_ROOT")
        if sdk_root:
            sdk = AndroidSDK(command=command, jdk=jdk, root_path=Path(sdk_root))

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

    The location pointed to by the ANDROID_SDK_ROOT environment
    variable:

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
            command=command,
            jdk=jdk,
            root_path=command.tools_path / "android_sdk"
        )

        if sdk.exists():
            # Ensure licenses have been accepted
            sdk.verify_license()
            return sdk

        if install:
            sdk.install()
            return sdk
        else:
            raise MissingToolError('Android SDK')

    def exists(self):
        """Confirm that the SDK actually exists.

        Look for the sdkmanager; and, if necessary, confirm that it is
        executable.
        """
        return self.sdkmanager_path.exists() and (
            self.command.host_os == "Windows"
            or self.command.os.access(self.sdkmanager_path, self.command.os.X_OK)
        )

    @property
    def managed_install(self):
        "Is the Android SDK install managed by Briefcase?"
        # Although the end-user can provide their own SDK, the SDK also
        # provides a built-in upgrade mechanism. Therefore, all Android SDKs
        # are managed installs.
        return True

    def install(self):
        """
        Download and install the Android SDK.
        """
        try:
            sdk_zip_path = self.command.download_url(
                url=self.sdk_url, download_path=self.command.tools_path,
            )
        except requests_exceptions.ConnectionError:
            raise NetworkFailure("download Android SDK")

        try:
            print("Install Android SDK...")
            # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
            self.command.shutil.unpack_archive(os.fsdecode(sdk_zip_path), extract_dir=os.fsdecode(self.root_path))
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
        if self.command.host_os != "Windows":
            for binpath in (self.root_path / "tools" / "bin").glob("*"):
                if not self.command.os.access(binpath, self.command.os.X_OK):
                    binpath.chmod(0o755)

        # Licences must be accepted.
        self.verify_license()

    def upgrade(self):
        """Upgrade the Android SDK"""
        try:
            # Using subprocess.run() with no I/O redirection so the user sees
            # the full output and can send input.
            self.command.subprocess.run(
                [os.fsdecode(self.sdkmanager_path), "--update"], env=self.env, check=True,
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                """\
    Error while reviewing Android SDK licenses. Please run this command and examine
    its output for errors.

    $ {sdkmanager} --update""".format(
                    sdkmanager=self.root_path / "tools" / "bin" / "sdkmanager"
                )
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
                [os.fsdecode(self.sdkmanager_path), "--licenses"], env=self.env, check=True,
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
                    os.fsdecode(self.sdkmanager_path),
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
                [os.fsdecode(self.emulator_path), "-list-avds"],
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
                [os.fsdecode(self.adb_path), "devices", "-l"],
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            ).strip()

            # Process the output of `adb devices -l`.
            # The first line is header information.
            # Each subsequent line is a single device descriptor.
            devices = {}
            header_found = False
            for line in output.split("\n"):
                if line == 'List of devices attached':
                    header_found = True
                elif header_found and line:
                    parts = re.sub(r"\s+", " ", line).split(" ")

                    details = {}
                    for part in parts[2:]:
                        key, value = part.split(":")
                        details[key] = value

                    if parts[1] == "device":
                        name = details["model"].replace("_", " ")
                        authorized = True
                    elif parts[1] == "offline":
                        name = "Unknown device (offline)"
                        authorized = False
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
        Select a device to be the target for actions.

        Interrogates the system to get the list of available devices.

        If the user has specified a device at the command line, that device
        will be validated, and then automatically selected.

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
        # If the device is a virtual device, use ADB to get the emulator AVD name.
        # If it is a physical device, use the device name.
        # Keep a log of all running AVDs
        running_avds = {}
        for d, details in sorted(running_devices.items(), key=lambda d: d[1]["name"]):
            name = details["name"]
            avd = self.adb(d).avd_name()
            if avd:
                # It's a running emulator
                running_avds[avd] = d
                full_name = "@{avd} (running emulator)".format(
                    avd=avd,
                )
                choices.append((d, full_name))

                # Save the AVD as a device detail.
                details["avd"] = avd

                # Device can be looked up by device ID or AVD
                device_choices[d] = full_name
                device_choices["@" + avd] = full_name
            else:
                # It's a physical device (might be disabled)
                full_name = "{name} ({d})".format(name=name, d=d)
                choices.append((d, full_name))
                device_choices[d] = full_name

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
        try:
            choice = select_option(choices, input=self.command.input)
        except InputDisabled:
            # If input is disabled, and there's only one actual simulator,
            # select it. If there are no simulators, select "Create simulator"
            if len(choices) <= 2:
                choice = choices[0][0]
            else:
                raise BriefcaseCommandError(
                    "Input has been disabled; can't select a device to target."
                )

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
            print("""
In future, you can specify this device by running:

    briefcase run android -d @{avd}

""".format(avd=avd))
        elif device:
            print("""
In future, you can specify this device by running:

    briefcase run android -d {device}

""".format(device=device))

        return device, name, avd

    def create_emulator(self):
        """Create a new Android emulator.

        :returns: The AVD of the newly created emulator.
        """
        # Get the list of existing emulators
        emulators = set(self.emulators())

        default_avd = 'beePhone'
        i = 1
        # Make sure the default name is unique
        while default_avd in emulators:
            i += 1
            default_avd = 'beePhone{i}'.format(i=i)

        # Prompt for a device avd until a valid one is provided.
        print("""
You need to select a name for your new emulator. This is an identifier that
can be used to start the emulator in future. It should follow the same naming
conventions as a Python package (i.e., it may only contain letters, numbers,
hyphens and underscores). If you don't provide a name, Briefcase will use the
a default name '{default_avd}'.

""".format(default_avd=default_avd))
        avd_is_invalid = True
        while avd_is_invalid:
            avd = self.command.input("Emulator name [{default_avd}]: ".format(
                default_avd=default_avd
            ))
            # If the user doesn't provide a name, use the default.
            if avd == '':
                avd = default_avd

            if not PEP508_NAME_RE.match(avd):
                print("""
'{avd}' is not a valid emulator name. An emulator name may only contain
letters, numbers, hyphens and underscores

""".format(avd=avd))
            elif avd in emulators:
                print("""
An emulator named '{avd}' already exists.

""".format(avd=avd))
                print()
            else:
                avd_is_invalid = False

        # TODO: Provide a list of options for device types with matching skins
        device_type = 'pixel'
        skin = 'pixel_3a'

        try:
            print()
            print("Creating Android emulator {avd}...".format(avd=avd))
            print()
            self.command.subprocess.check_output(
                [
                    os.fsdecode(self.avdmanager_path),
                    "--verbose",
                    "create", "avd",
                    "--name", avd,
                    "--abi", "x86",
                    "--package", 'system-images;android-28;default;x86',
                    "--device", device_type,
                ],
                env=self.env,
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError("Unable to create Android emulator")

        # Check for a device skin. If it doesn't exist, download it.
        skin_path = self.root_path / "skins" / skin
        if skin_path.exists():
            print("Device skin '{skin}' already exists".format(skin=skin))
        else:
            print("Obtaining device skin...")
            skin_url = (
                "https://android.googlesource.com/platform/tools/adt/idea/"
                "+archive/refs/heads/mirror-goog-studio-master-dev/"
                "artwork/resources/device-art-resources/{skin}.tar.gz".format(skin=skin)
            )

            try:
                skin_tgz_path = self.command.download_url(
                    url=skin_url,
                    download_path=self.root_path,
                )
            except requests_exceptions.ConnectionError:
                raise NetworkFailure("download {skin} device skin".format(skin=skin))

            # Unpack skin archive
            try:
                # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
                self.command.shutil.unpack_archive(
                    os.fsdecode(skin_tgz_path),
                    extract_dir=os.fsdecode(skin_path)
                )
            except (shutil.ReadError, EOFError):
                raise BriefcaseCommandError(
                    "Unable to unpack {skin} device skin".format(skin=skin)
                )

            # Delete the downloaded file.
            skin_tgz_path.unlink()

        print("Adding extra device configuration...")
        with (
            self.avd_path / '{avd}.avd'.format(avd=avd) / 'config.ini'
        ).open('a') as f:
            f.write("""
disk.dataPartition.size=4096M
hw.keyboard=yes
skin.dynamic=yes
skin.name={skin}
skin.path=skins/{skin}
showDeviceFrame=yes
""".format(skin=skin))

            print("""
Android emulator '{avd}' created.

In future, you can specify this device by running:

    briefcase run android -d @{avd}
""".format(avd=avd))

        return avd

    def start_emulator(self, avd):
        """Start an existing Android emulator.

        Returns when the emulator is booted and ready to accept apps.

        :param avd: The AVD of the device.
        """
        if avd in set(self.emulators()):
            print("Starting emulator {avd}...".format(avd=avd))
            emulator_popen = self.command.subprocess.Popen(
                [
                    os.fsdecode(self.emulator_path),
                    '@' + avd,
                    '-dns-server', '8.8.8.8'
                ],
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # The boot process happens in 2 phases.
            # First, the emulator appears in the device list. However, it's
            # not ready until the boot process has finished. To determine
            # the boot status, we need the device ID, and an ADB connection.

            # Step 1: Wait for the device to appear so we can get an
            # ADB instance for the new device.
            print()
            print('Waiting for emulator to start...', flush=True, end='')
            adb = None
            known_devices = set()
            while adb is None:
                print('.', flush=True, end='')
                if emulator_popen.poll() is not None:
                    raise BriefcaseCommandError("""
Android emulator was unable to start!

Try starting the emulator manually by running:

    {cmdline}

Resolve any problems you discover, then try running your app again. You may
find this page helpful in diagnosing emulator problems.

    https://developer.android.com/studio/run/emulator-acceleration#accel-vm
""".format(cmdline=' '.join(str(arg) for arg in emulator_popen.args)))

                for device, details in sorted(self.devices().items()):
                    # Only process authorized devices that we haven't seen.
                    if details['authorized'] and device not in known_devices:
                        adb = self.adb(device)
                        device_avd = adb.avd_name()

                        if device_avd == avd:
                            # Found an active device that matches
                            # the AVD we are starting.
                            full_name = "@{avd} (running emulator)".format(
                                avd=avd,
                            )
                            break
                        else:
                            # Not the one. Zathras knows.
                            adb = None
                            known_devices.add(device)

                # Try again in 2 seconds...
                self.sleep(2)

            # Print a marker so we can see the phase change
            print(' booting...', flush=True, end='')

            # Phase 2: Wait for the boot process to complete
            while not adb.has_booted():
                if emulator_popen.poll() is not None:
                    raise BriefcaseCommandError("""
Android emulator was unable to boot!

Try starting the emulator manually by running:

    {cmdline}

Resolve any problems you discover, then try running your app again. You may
find this page helpful in diagnosing emulator problems.

    https://developer.android.com/studio/run/emulator-acceleration#accel-vm
""".format(cmdline=' '.join(str(arg) for arg in emulator_popen.args)))

                # Try again in 2 seconds...
                self.sleep(2)
                print('.', flush=True, end='')

            print()
            # Return the device ID and full name.
            return device, full_name
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

    def has_booted(self):
        """Determine if the device has completed booting.

        :returns True if it has booted; False otherwise.
        """
        try:
            # When the sys.boot_completed property of the device
            # returns '1', the boot is complete. Any other response indicates
            # booting is underway.
            output = self.run('shell', 'getprop', 'sys.boot_completed')
            return output.strip() == '1'
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Unable to determine if emulator {device} has booted.".format(
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
                    os.fsdecode(self.android_sdk.adb_path),
                    "-s",
                    self.device,
                ]
                + [(os.fsdecode(arg) if isinstance(arg, Path) else arg) for arg in arguments],
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
            self.run("install", apk_path)
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

    def clear_log(self):
        """
        Clear the log for the device.

        Returns `None` on success; raises an exception on failure.
        """
        try:
            # Invoke `adb logcat -c`
            self.run("logcat", "-c")
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Unable to clear log on {device}".format(
                    device=self.device,
                )
            )

    def logcat(self):
        """
        Start tailing the adb log for the device.
        """
        try:
            # Using subprocess.run() with no I/O redirection so the user sees
            # the full output and can send input.
            self.command.subprocess.run(
                [
                    os.fsdecode(self.android_sdk.adb_path),
                    "-s",
                    self.device,
                    "logcat",
                    "-s",
                    "MainActivity:*",
                    "stdio:*",
                    "Python:*",
                ],
                env=self.android_sdk.env,
                check=True,
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError("Error starting ADB logcat.")
