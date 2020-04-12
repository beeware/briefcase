import re
import shutil
import subprocess
from pathlib import Path

from requests import exceptions as requests_exceptions

from briefcase.exceptions import (
    BriefcaseCommandError,
    InvalidDeviceError,
    NetworkFailure
)

DEVICE_NOT_FOUND = re.compile(r"^error: device '[^']*' not found")


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
    sdk_root = command.os.environ.get('ANDROID_SDK_ROOT')
    if sdk_root:
        sdk = AndroidSDK(command=command, root_path=Path(sdk_root))

        if sdk.exists():
            # Ensure licenses have been accepted
            sdk.verify_license()
            return sdk
        else:
            print("""
*************************************************************************
** WARNING: ANDROID_SDK_ROOT does not point to an Android SDK          **
*************************************************************************

    The location pointed to by the ANDROID_SDK_ROOT environment variable:

     {sdk_root}

    doesn't appear to contain an Android SDK.

    Briefcase will use its own SDK instance.

*************************************************************************

""".format(sdk_root=sdk_root))

    # Build an SDK wrapper for the Briefcase SDK instance.
    sdk = AndroidSDK(
        command=command,
        root_path=command.dot_briefcase_path / "tools" / "android_sdk"
    )

    if sdk.exists():
        # Ensure licenses have been accepted
        sdk.verify_license()
        return sdk

    print("Setting up Android SDK...")
    try:
        sdk_zip_path = command.download_url(
            url=sdk.sdk_url,
            download_path=command.dot_briefcase_path / "tools",
        )
    except requests_exceptions.ConnectionError:
        raise NetworkFailure("download Android SDK")
    try:
        command.shutil.unpack_archive(
            str(sdk_zip_path),
            extract_dir=str(sdk.root_path)
        )
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
        sdkmanager = "sdkmanager.bat" if self.command.host_os == "Windows" else "sdkmanager"
        return self.root_path / "tools" / "bin" / sdkmanager

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
                [str(self.sdkmanager_path), "--licenses"],
                env=self.env,
                check=True,
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
                check=True
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
                [
                    str(self.root_path / "emulator" / "emulator"),
                    "-list-avds",
                ],
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            ).strip()

            # AVD names are returned one per line.
            if len(output) == 0:
                return []
            return output.split('\n')
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError("Unable to obtain Android emulator list")

    def devices(self):
        """Find the devices that are attached and available to ADB

        """
        try:
            # Capture `stderr` so that if the process exits with failure, the
            # stderr data is in `e.output`.
            output = self.command.subprocess.check_output(
                [
                    str(self.root_path / "platform-tools" / "adb"),
                    "devices",
                    "-l",
                ],
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            ).strip()

            # Process the output of `adb devices -l`.
            # The first line is header information.
            # Each subsequent line is a single device descriptor.
            devices = {}
            for line in output.split('\n')[1:]:
                parts = re.sub(r'\s+', ' ', line).split(' ')

                details = {}
                for part in parts[2:]:
                    key, value = part.split(':')
                    details[key] = value

                if parts[1] == 'device':
                    name = details['device']
                    authorized = True
                else:
                    name = "Unknown device (not authorized for development)"
                    authorized = False

                devices[parts[0]] = {
                    'name': name,
                    'authorized': authorized,
                }

            return devices
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError("Unable to obtain Android device list")


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
            output = self.run('emu', 'avd', 'name')
            return output.split('\n')[0]
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
                    self.device
                ] + list(arguments),
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            if any((DEVICE_NOT_FOUND.match(line) for line in e.output.split("\n"))):
                raise InvalidDeviceError('device id', self.device)
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
                    apk_path=apk_path,
                    device=self.device,
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
                    package=package,
                    device=self.device,
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
                raise BriefcaseCommandError("""\
    Activity class not found while starting app.

    `adb` output:

    {output}""".format(output=output))
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Unable to start {package}/{activity} on {device}".format(
                    package=package,
                    activity=activity,
                    device=self.device,
                )
            )
