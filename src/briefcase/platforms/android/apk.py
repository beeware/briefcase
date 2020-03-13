import subprocess
from pathlib import Path
from stat import S_IMODE
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
from briefcase.integrations.adb import (
    no_or_wrong_device_message,
    force_stop_app,
    install_apk,
    start_app,
)


class ApkMixin:
    output_format = "apk"
    platform = "android"
    dot_briefcase = Path.home() / ".briefcase"

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
        return self.dot_briefcase / "tools" / "android_sdk"

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
        # If the SDK tools don't exist or aren't executable, install the SDK.
        # TODO: Reconsider this for Windows.
        tools_path = self.sdk_path / "tools" / "bin"
        tools_ok = (
            tools_path.exists()
            and all(
                [
                    S_IMODE(tool.stat().st_mode) == 0o755
                    for tool in tools_path.glob("*")
                ]
            )
            and (tools_path / "sdkmanager").exists()
        )
        if tools_ok:
            return

        print("Setting up Android SDK...")
        try:
            sdk_zip_path = self.download_url(
                url=self.sdk_url,
                download_path=self.dot_briefcase / "tools",
            )
        except requests_exceptions.ConnectionError:
            raise NetworkFailure("download Android SDK")
        try:
            with ZipFile(str(sdk_zip_path)) as sdk_zip:
                sdk_zip.extractall(path=str(self.sdk_path))
        except BadZipFile:
            raise BriefcaseCommandError(
                """\
Invalid ZIP file found at {sdk_zip_path}

Partial download? Remove it, then try again.""".format(
                    sdk_zip_path=sdk_zip_path
                )
            )
        sdk_zip_path.unlink()  # Zip file no longer needed once unpacked.
        for binpath in tools_path.glob("*"):
            binpath.chmod(0o755)

    def verify_license(self):
        license_path = self.sdk_path / "licenses" / "android-sdk-license"
        if license_path.exists():
            return

        print("\nPlease accept `android-sdk-license` when prompted.\n")
        try:
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
        if (self.sdk_path / "emulator").exists():
            return

        print("Ensuring we have the Android emulator and system image...")
        try:
            self.subprocess.check_output(
                [
                    self.sdk_path / "tools" / "bin" / "sdkmanager",
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
Error while installing Android platform tools. Full gradle output:\n\n"""
                + e.output.decode("ascii", "replace")
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
                + no_or_wrong_device_message(self.sdk_path)
            )

        # Install the latest APK file onto the device.
        install_apk(self.sdk_path, device, self.binary_path(app))

        # Compute Android package name based on beeware `bundle` and `app_name`
        # app properties, similar to iOS.
        package = "{app.bundle}.{app.app_name}".format(app=app)

        # We force-stop the app to ensure the activity launches freshly.
        force_stop_app(self.sdk_path, device, package)

        # To start the app, we launch `org.beeware.android.MainActivity`.
        start_app(
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
