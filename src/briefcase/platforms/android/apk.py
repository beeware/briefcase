import subprocess
from pathlib import Path
from zipfile import ZipFile

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
from briefcase.integrations.adb import force_stop_app, install_apk, start_app


class ApkMixin:
    output_format = "apk"
    platform = "android"

    @property
    def android_sdk_path(self):
        return Path.home() / ".briefcase" / "tools" / "android_sdk"

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
    def android_sdk_url(self):
        # TODO: Add test validating that, if this is mocked out for a sentinel
        # ZIP file, we surely unpack it into android_sdk_path.
        """The Android SDK URL appropriate to this operating system."""
        # The URLs described by the pattern below have existed since
        # approximately 2017, and the code they download has a built-in
        # updater. I hope they will work for many years.
        return "https://dl.google.com/android/repository/" + (
            "sdk-tools-{os}-4333796.zip".format(os=self.host_os.lower()))

    def verify_tools(self):
        """
        Verify that we can download a support package for this Python version,
        then ensure the Android development tools are installed.
        """
        if self.python_version_tag != "3.7":
            raise BriefcaseCommandError("""\
Found Python version {self.python_version_tag}. Android packaging currently
requires Python 3.7.""".format(self=self))

        if not self.android_sdk_path.exists():
            print("Setting up Android SDK...")
            try:
                android_sdk_zip_path = self.download_url(
                    url=self.android_sdk_url,
                    download_path=Path.home() / ".briefcase" / "tools",
                )
            except requests_exceptions.ConnectionError:
                raise NetworkFailure("downloading Android SDK")
            with ZipFile(android_sdk_zip_path) as android_sdk_zip:
                android_sdk_zip.extractall(path=self.android_sdk_path)
            # Remove the ZIP file; it has no purpose now that it is extracted.
            android_sdk_zip_path.unlink()
            # Set executable permissions. The ZipFile module does not extract
            # these permissions, but Linux & macOS need them.
            # TODO: Test this on Windows.
            tools_bin = self.android_sdk_path_tmp / "tools" / "bin"
            for binpath in tools_bin.glob('*'):
                binpath.chmod(0o755)

            print("Ensuring all Android SDK licenses are accepted...")
            try:
                self.subprocess.run(
                    [tools_bin / "sdkmanager", "--licenses"],
                    check=True,
                    cwd=self.android_sdk_path,
                )
            except subprocess.CalledProcessError:
                # TODO: Capture and print sdkmanager log, in case of error.
                raise BriefcaseCommandError(
                    "Error while reviewing Android SDK licenses"
                )


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
            self.subprocess.run(
                ["./gradlew", "assembleDebug"],
                env=dict(list(self.os.environ.items()) + [
                    ('ANDROID_SDK_ROOT', str(self.android_sdk_path))]),
                check=True,
                cwd=str(self.bundle_path(app)),
            )
        except subprocess.CalledProcessError:
            # TODO: Capture and print gradle log, in case of error.
            raise BriefcaseCommandError(
                "Error while building app {app.app_name}.".format(app=app)
            )


class ApkRunCommand(ApkMixin, RunCommand):
    description = "Run an Android APK."

    def verify_tools(self):
        super().verify_tools()
        if not (self.android_sdk_path / "emulator").exists():
            print("Ensuring we have the Android emulator and system image...")
            # TODO: Error handling.
            self.subprocess.run([
                self.android_sdk_path / "tools" / "bin" / "sdkmanager",
                "platforms;android-28",
                "system-images;android-28;default;x86",
                "emulator",
                "platform-tools",
            ])

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            '-d',
            '--device',
            dest='device',
            help='The device to target, formatted for `adb`',
            required=False,
        )

    def run_app(self, app: BaseConfig, device=None, **kwargs):
        """
        Start the application.

        :param app: The config object for the app
        :param device: The device to target. If ``None``, the user will
            be asked to re-run the command selecting a specific device.
        :param base_path: The path to the project directory.
        """
        if device is None:
            raise BriefcaseCommandError("""\
Please specify a specific device on which to run the app by passing
`-d device_name`.""".lstrip().format(
                adb=self.android_sdk_path / "platform-tools" / "adb",
                emulator=self.android_sdk_path / "emulator" / "emulator",
                tools_bin=self.android_sdk_path ,
            ))

        # Install the latest APK file onto the device.
        install_apk(self.android_sdk_path, device, self.binary_path(app))

        # Compute Android package name based on beeware `bundle` and `app_name`
        # app properties, similar to iOS.
        package = "{app.bundle}.{app.app_name}".format(app=app)

        # We force-stop the app to ensure the activity launches freshly.
        force_stop_app(self.android_sdk_path, device, package)

        # To start the app, we launch `org.beeware.android.MainActivity`.
        start_app(
            self.android_sdk_path, device, package,
            "org.beeware.android.MainActivity"
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
