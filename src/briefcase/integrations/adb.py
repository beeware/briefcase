import re
import subprocess

from briefcase.exceptions import BriefcaseCommandError

DEVICE_NOT_FOUND = re.compile(r"^error: device '[^']*' not found")


class ADB:
    def __init__(self, sdk_path, device, sub=subprocess):
        """
        An API integration for the Android Debug Bridge (ADB).

        :param sdk_path: The path to the Android SDK.
        :param device: The ID of the device to target (in a format usable by`adb -s`)
        :param sub: For testing purposes: the subprocess module to use.
        """
        self.sdk_path = sdk_path
        self.device = device
        self.subprocess = sub

    def command(self, *arguments):
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
            return self.subprocess.check_output(
                [
                    str(self.sdk_path / "platform-tools" / "adb"),
                    "-s",
                    self.device
                ] + list(arguments),
                stderr=self.subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            # Decode the output as ASCII. If it contains data in another
            # character set, ignore that issue. We're looking for a ASCII-only
            # error message.
            output = e.output.decode("ascii", "replace")
            if any((DEVICE_NOT_FOUND.match(line) for line in output.split("\n"))):
                raise BriefcaseCommandError(no_or_wrong_device_message(self.sdk_path))
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
        return self.command("install", str(apk_path))

    def force_stop_app(self, package):
        """
        Force-stop an app, specified as a package name.

        :param package: The name of the Android package, e.g., com.username.myapp.

        Returns `None` on success; raises an exception on failure.
        """
        # In my testing, `force-stop` exits with status code 0 (success) so long
        # as you pass a package name, even if the package does not exist, or the
        # package is not running.
        self.command("shell", "am", "force-stop", package)

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
        output = self.command(
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


def no_or_wrong_device_message(sdk_path):
    adb_path = sdk_path / "platform-tools" / "adb"
    avdmanager_path = sdk_path / "tools" / "bin" / "avdmanager"
    emulator_path = sdk_path / "emulator" / "emulator"
    sdkmanager_path = sdk_path / "tools" / "bin" / "sdkmanager"
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
