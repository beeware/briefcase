import re
import shutil
import subprocess

from requests import exceptions as requests_exceptions

from briefcase.exceptions import BriefcaseCommandError, NetworkFailure

DEVICE_NOT_FOUND = re.compile(r"^error: device '[^']*' not found")


def verify_android_sdk(command):
    """
    Verify the Android SDK is available.

    If no Android SDK is available, the base SDK is downloaded.

    :param command: The command making the verification request.
    :returns: An AndroidSDK instance, bound to command.
    """
    # On Windows, the Android SDK makes some files executable by adding `.bat` to
    # the end of their filenames.
    #
    # On macOS & Linux, `verify_android_sdk()` takes care to chmod some files so that
    # they are marked executable.
    #
    # On all platforms, we need to unpack the Android SDK ZIP file.
    #
    # If we've already done this, we can exit early.
    sdk = AndroidSDK(
        command=command,
        root_path=command.dot_briefcase_path / "tools" / "android_sdk"
    )

    if sdk.sdkmanager_path.exists() and (
        command.host_os == "Windows"
        or command.os.access(str(sdk.sdkmanager_path), command.os.X_OK)
    ):
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

    def adb(self, device):
        return ADB(self.sdk, device=device)

    def verify_license(self):
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

    def no_or_wrong_device_message(self):
        adb_path = self.root_path / "platform-tools" / "adb"
        avdmanager_path = self.root_path / "tools" / "bin" / "avdmanager"
        emulator_path = self.root_path / "emulator" / "emulator"
        sdkmanager_path = self.root_path / "tools" / "bin" / "sdkmanager"
        return """\
You can get a list of valid devices by running this command:

    $ {adb_path} devices -l

The device ID is the value in the first column of output - it will be either:

  * a ~12-16 character alphanumeric string (for a physical device); or
  * a value like `emulator-5554` (for an emulator).

If you do not see any devices, you can create and start an emulator by running:

    $ {sdkmanager_path} "platforms;android-28" \
"system-images;android-28;default;x86" "emulator" "platform-tools"

    $ {avdmanager_path} --verbose create avd \
--name robotfriend --abi x86 \
--package 'system-images;android-28;default;x86' --device pixel

    $ echo 'disk.dataPartition.size=4096M' >> $HOME/.android/avd/robotfriend.avd/config.ini

    $ {emulator_path} -avd robotfriend &

""".format(
            adb_path=adb_path,
            avdmanager_path=avdmanager_path,
            emulator_path=emulator_path,
            sdkmanager_path=sdkmanager_path,
        )


class ADB:
    def __init__(self, android_sdk, device):
        """
        An API integration for the Android Debug Bridge (ADB).

        :param android_sdk: The Android SDK providing ADB.
        :param device: The ID of the device to target (in a format usable by`adb -s`)
        """
        self.android_sdk = android_sdk
        self.command = android_sdk.command
        self.device = device

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
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            # Decode the output as ASCII. If it contains data in another
            # character set, ignore that issue. We're looking for a ASCII-only
            # error message.
            output = e.output.decode("ascii", "replace")
            if any((DEVICE_NOT_FOUND.match(line) for line in output.split("\n"))):
                raise BriefcaseCommandError(self.android_sdk.no_or_wrong_device_message())
            raise BriefcaseCommandError(
                """\
    Unable to run command on device. Received this output from `adb`
    {output}""".format(
                    output=output
                )
            )

    def install_apk(self, apk_path):
        """
        Install an APK file on an Android device.

        :param apk_path: The path of the Android APK file to install.

        Returns `None` on success; raises an exception on failure.
        """
        return self.run("install", str(apk_path))

    def force_stop_app(self, package):
        """
        Force-stop an app, specified as a package name.

        :param package: The name of the Android package, e.g., com.username.myapp.

        Returns `None` on success; raises an exception on failure.
        """
        # In my testing, `force-stop` exits with status code 0 (success) so long
        # as you pass a package name, even if the package does not exist, or the
        # package is not running.
        self.run("shell", "am", "force-stop", package)

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
        ).decode("ascii", "replace")

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
