import subprocess
import re

from briefcase.exceptions import BriefcaseCommandError


class DeviceNotFound(Exception):
    pass


DEVICE_NOT_FOUND = re.compile(r"^error: device '[^']*' not found")


def run_adb(sdk_path, device, arguments, sub=subprocess):
    """
    Run a command on a device using Android debug bridge, `adb`. The device
    name is mandatory to ensure clarity in the case of multiple attached
    devices.

    :param sdk_path: The path of the Android SDK to use.
    :param device: The name of the device in a format usable by `adb -s`.
    :param arguments: List of strings to pass to `adb` as arguments.

    Returns `None` on success; raises an exception on failure.
    """
    # The ADB integration operates on the basis of running commands before
    # checking that they are valid, then parsing output to notice errors.
    # This keeps performance good in the success case.
    try:
        # Capture `stderr` so that if the process exits with failure, the
        # stderr data is in `e.output`.
        sub.check_output(
            [str(sdk_path / 'platform-tools' / 'adb')] + ['-s', device] +
            arguments,
            stderr=sub.STDOUT)
    except subprocess.CalledProcessError as e:
        # Decode the output as ASCII. If it contains data in another
        # character set, ignore that issue. We're looking for a ASCII-only
        # error message.
        output = e.output.decode('ascii', 'replace')
        if any((DEVICE_NOT_FOUND.match(line) for line in output.split('\n'))):
            raise DeviceNotFound()
        raise BriefcaseCommandError("""\
Unable to run command on device. Received this output from `adb`
{output}""".format(output=output))


def install_apk(sdk_path, device, apk_path, sub=subprocess):
    """
    Install an APK file on an Android device.

    :param sdk_path: The path of the Android SDK to use.
    :param device: The name of the device in a format usable by `adb -s`.
    :param apk_path: The path of the Android APK file to install.

    Returns `None` on success; raises an exception on failure.
    """
    print("Installing app on device...")
    return run_adb(sdk_path, device, ['install', str(apk_path)])


def force_stop_app(sdk_path, device, package, sub=subprocess):
    """
    Force-stop an app, specified as a package name.

    :param sdk_path: The path of the Android SDK to use.
    :param device: The name of the device in a format usable by `adb -s`.
    :param package: The name of the Android package, e.g., com.username.myapp.

    Returns `None` on success; raises an exception on failure.
    """
    # In my testing, `force-stop` exits with status code 0 (success) so long
    # as you pass a package name, even if the package does not exist, or the
    # package is not running.
    # TODO: Think about output and error cases.
    print("Stopping app if running...")
    return run_adb(sdk_path, device, ['shell', 'am', 'force-stop', package])


def start_app(sdk_path, device, package, activity, sub=subprocess):
    """
    Start an app, specified as a package name & activity name.

    :param sdk_path: The path of the Android SDK to use.
    :param device: The name of the device in a format usable by `adb -s`.
    :param package: The name of the Android package, e.g., com.username.myapp.
    :param apk_path: The path of the Android APK file to install.

    Returns `None` on success; raises an exception on failure.

    If you have an APK file, and you are not sure of the package or activity
    name, you can find it using `aapt dump badging filename.apk` and looking
    for "package" and "launchable-activity" in the output.
    """
    print("Launching app...")
    return run_adb(
        sdk_path, device, [
            'shell', 'am', 'start',
            "{package}/{activity}".format(package=package, activity=activity),
            '-a', 'android.intent.action.MAIN', '-c',
            'android.intent.category.LAUNCHER'
        ])
