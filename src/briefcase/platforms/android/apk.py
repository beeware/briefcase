import subprocess
from zipfile import BadZipFile, ZipFile

from requests import exceptions as requests_exceptions

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError, NetworkFailure
from briefcase.integrations import adb


class ApkMixin:
    output_format = "apk"
    platform = "android"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.adb = adb  # Storing for easy override by unit tests.

    def binary_path(self, app):
        return (
            self.platform_path
            / app.formal_name
            / "app"
            / "build"
            / "outputs"
            / "apk"
            / "debug"
            / "app-debug.apk"
        )

    def distribution_path(self, app):
        return self.binary_path(app)

    @property
    def sdk_path(self):
        return self.dot_briefcase_path / "tools" / "android_sdk"

    @property
    def sdk_url(self):
        """The Android SDK URL appropriate to the current operating system."""
        # The URLs described by the pattern below have existed since
        # approximately 2017, and the code they download has a built-in
        # updater. I hope they will work for many years.
        return "https://dl.google.com/android/repository/" + (
            "sdk-tools-{os}-4333796.zip".format(os=self.host_os.lower())
        )

    def verify_python_version(self):
        if self.python_version_tag != "3.7":
            raise BriefcaseCommandError(
                """\
Found Python version {self.python_version_tag}. Android packaging currently
requires Python 3.7.""".format(
                    self=self
                )
            )

    def verify_sdk(self):
        """
        Install the Android SDK if needed.
        """
        tools_path = self.sdk_path / "tools" / "bin"
        sdkmanager_exe = "sdkmanager.exe" if self.host_os == "Windows" else "sdkmanager"
        # This method marks some files as executable, so `tools_ok` checks for
        # that as well. On Windows, all generated files are executable.
        tools_ok = (
            tools_path.exists()
            and all(
                [
                    self.os.access(str(tool), self.os.X_OK)
                    for tool in tools_path.glob("*")
                ]
            )
            and (tools_path / sdkmanager_exe).exists()
        )
        if tools_ok:
            return

        print("Setting up Android SDK...")
        try:
            sdk_zip_path = self.download_url(
                url=self.sdk_url, download_path=self.dot_briefcase_path / "tools",
            )
        except requests_exceptions.ConnectionError:
            raise NetworkFailure("download Android SDK")
        try:
            with ZipFile(str(sdk_zip_path)) as sdk_zip:
                sdk_zip.extractall(path=str(self.sdk_path))
        except BadZipFile:
            raise BriefcaseCommandError(
                """\
Unable to unpack Android SDK ZIP file. The download may have been interrupted
or corrupted.

Delete {sdk_zip_path} and run briefcase again.""".format(
                    sdk_zip_path=sdk_zip_path
                )
            )
        sdk_zip_path.unlink()  # Zip file no longer needed once unpacked.
        # `ZipFile` ignores the permission metadata in the Android SDK ZIP
        # file, so we manually fix permissions.
        for binpath in tools_path.glob("*"):
            if not self.os.access(str(binpath), self.os.X_OK):
                binpath.chmod(0o755)

    def verify_license(self):
        license_path = self.sdk_path / "licenses" / "android-sdk-license"
        if license_path.exists():
            return

        print(
            "\n"
            + """\
To use briefcase with the Android SDK provided by Google, you must accept
`android-sdk-license`.

Running the Android SDK license tool...\n"""
        )
        try:
            # Using subprocess.run() with no I/O redirection so the user sees
            # the full output and can send input.
            self.subprocess.run(
                ["./sdkmanager", "--licenses"],
                check=True,
                cwd=str(self.sdk_path / "tools" / "bin"),
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                """\
Error while reviewing Android SDK licenses. Please run this command and examine
its output for errors.

$ {sdkmanager} --licenses""".format(
                    sdkmanager=self.sdk_path / "tools" / "bin" / "sdkmanager"
                )
            )

        if not license_path.exists():
            raise BriefcaseCommandError(
                """\
You did not accept the Android SDK license. Please re-run the briefcase command
and accept the Android SDK license when prompted. You may need an Internet
connection."""
            )

    def verify_tools(self):
        """
        Verify that we the Android APK tools in `briefcase` will operate on
        this system, downloading tools as needed.
        """
        self.verify_python_version()
        self.verify_sdk()
        self.verify_license()


class ApkCreateCommand(ApkMixin, CreateCommand):
    description = "Create and populate an Android APK."


class ApkUpdateCommand(ApkMixin, UpdateCommand):
    description = "Update an existing Android APK."


class ApkBuildCommand(ApkMixin, BuildCommand):
    description = "Build an Android APK."

    def build_app(self, app: BaseConfig, **kwargs):
        """
        Build an application.

        :param app: The application to build
        """
        print("[{app.app_name}] Building Android APK...".format(app=app))
        try:
            env = {**self.os.environ, "ANDROID_SDK_ROOT": str(self.sdk_path)}
            self.subprocess.check_output(
                ["./gradlew", "assembleDebug"],
                env=env,
                cwd=str(self.bundle_path(app)),
                stderr=self.subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                "Error while building. Full gradle output:\n\n"
                + e.output.decode("ascii", "replace")
            )


class ApkRunCommand(ApkMixin, RunCommand):
    description = "Run an Android APK."

    def verify_tools(self):
        super().verify_tools()
        self.verify_emulator()

    def verify_emulator(self):
        if (self.sdk_path / "emulator").exists():
            return

        print("Downloading the Android emulator and system image...")
        try:
            # Using `check_output` and `stderr=STDOUT` so we buffer output,
            # displaying it only if an exception occurs.
            self.subprocess.check_output(
                [
                    str(self.sdk_path / "tools" / "bin" / "sdkmanager"),
                    "platforms;android-28",
                    "system-images;android-28;default;x86",
                    "emulator",
                    "platform-tools",
                ],
                stderr=self.subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                """\
Error while installing Android emulator and system image.

`sdkmanager` exited with {e.returncode}.

Full `sdkmanager` output:

{output}
""".format(
                    output=e.output.decode("ascii", "replace"), e=e
                )
            )

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "-d",
            "--device",
            dest="device",
            help="The device to target, formatted for `adb`",
            required=False,
        )

    def run_app(self, app: BaseConfig, device=None, **kwargs):
        """
        Start the application.

        :param app: The config object for the app
        :param device: The device to target. If ``None``, the user will
            be asked to re-run the command selecting a specific device.
        """
        if device is None:
            raise BriefcaseCommandError(
                """\
Please specify a specific device on which to run the app by passing
`-d device_name`.\n\n"""
                + self.adb.no_or_wrong_device_message(self.sdk_path)
            )

        # Install the latest APK file onto the device.
        self.adb.install_apk(self.sdk_path, device, self.binary_path(app))

        # Compute Android package name based on beeware `bundle` and `app_name`
        # app properties, similar to iOS.
        package = "{app.bundle}.{app.app_name}".format(app=app)

        # We force-stop the app to ensure the activity launches freshly.
        self.adb.force_stop_app(self.sdk_path, device, package)

        # To start the app, we launch `org.beeware.android.MainActivity`.
        self.adb.start_app(
            self.sdk_path, device, package, "org.beeware.android.MainActivity"
        )


class ApkPackageCommand(ApkMixin, PackageCommand):
    description = "Package an Android APK."


class ApkPublishCommand(ApkMixin, PublishCommand):
    description = "Publish an Android APK."


# Declare the briefcase command bindings
create = ApkCreateCommand  # noqa
update = ApkUpdateCommand  # noqa
build = ApkBuildCommand  # noqa
run = ApkRunCommand  # noqa
package = ApkPackageCommand  # noqa
publish = ApkPublishCommand  # noqa
