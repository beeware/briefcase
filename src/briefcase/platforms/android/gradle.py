import shutil
import subprocess

from requests import exceptions as requests_exceptions

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError, NetworkFailure
from briefcase.integrations.adb import ADB, no_or_wrong_device_message
from briefcase.integrations.java import verify_jdk


class GradleMixin:
    output_format = "gradle"
    platform = "android"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ADB = ADB  # Storing for easy override by unit tests.

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
    def sdkmanager_path(self):
        sdkmanager = "sdkmanager.bat" if self.host_os == "Windows" else "sdkmanager"
        return self.sdk_path / "tools" / "bin" / sdkmanager

    @property
    def android_env(self):
        return {
            **self.os.environ,
            "ANDROID_SDK_ROOT": str(self.sdk_path),
            "JAVA_HOME": str(self.java_home_path),
        }

    def gradlew_path(self, app):
        gradlew = "gradlew.bat" if self.host_os == "Windows" else "gradlew"
        return self.bundle_path(app) / gradlew

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
        # On Windows, the Android SDK makes some files executable by adding `.bat` to
        # the end of their filenames.
        #
        # On macOS & Linux, `verify_sdk()` takes care to chmod some files so that
        # they are marked executable.
        #
        # On all platforms, we need to unpack the Android SDK ZIP file.
        #
        # If we've already done this, we can exit early.
        if self.sdkmanager_path.exists() and (
            self.host_os == "Windows"
            or self.os.access(str(self.sdkmanager_path), self.os.X_OK)
        ):
            return

        print("Setting up Android SDK...")
        try:
            sdk_zip_path = self.download_url(
                url=self.sdk_url, download_path=self.dot_briefcase_path / "tools",
            )
        except requests_exceptions.ConnectionError:
            raise NetworkFailure("download Android SDK")
        try:
            self.shutil.unpack_archive(
                str(sdk_zip_path),
                extract_dir=str(self.sdk_path)
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
        sdk_zip_path.unlink()  # Zip file no longer needed once unpacked.
        # Python zip unpacking ignores permission metadata.
        # On non-Windows, we manually fix permissions.
        if self.host_os == "Windows":
            return
        for binpath in (self.sdk_path / "tools" / "bin").glob("*"):
            if not self.os.access(str(binpath), self.os.X_OK):
                binpath.chmod(0o755)

    def verify_license(self):
        license_path = self.sdk_path / "licenses" / "android-sdk-license"
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
            self.subprocess.run(
                [str(self.sdkmanager_path), "--licenses"],
                env=self.android_env,
                check=True,
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
You did not accept the Android SDK licenses. Please re-run the briefcase command
and accept the Android SDK license when prompted. You may need an Internet
connection."""
            )

    def verify_tools(self):
        """
        Verify that we the Android APK tools in `briefcase` will operate on
        this system, downloading tools as needed.
        """
        super().verify_tools()
        self.verify_python_version()
        self.java_home_path = verify_jdk(self)
        self.verify_sdk()
        self.verify_license()


class GradleCreateCommand(GradleMixin, CreateCommand):
    description = "Create and populate an Android APK."


class GradleUpdateCommand(GradleMixin, UpdateCommand):
    description = "Update an existing Android APK."


class GradleBuildCommand(GradleMixin, BuildCommand):
    description = "Build an Android APK."

    def build_app(self, app: BaseConfig, **kwargs):
        """
        Build an application.

        :param app: The application to build
        """
        print("[{app.app_name}] Building Android APK...".format(app=app))
        try:
            self.subprocess.run(
                # Windows needs the full path to `gradlew`; macOS & Linux can find it
                # via `./gradlew`. For simplicity of implementation, we always provide
                # the full path.
                [str(self.gradlew_path(app)), "assembleDebug"],
                env=self.android_env,
                # Set working directory so gradle can use the app bundle path as its
                # project root, i.e., to avoid 'Task assembleDebug not found'.
                cwd=str(self.bundle_path(app)),
                check=True
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError("Error while building project.")


class GradleRunCommand(GradleMixin, RunCommand):
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
            self.subprocess.run(
                [
                    str(self.sdkmanager_path),
                    "platforms;android-28",
                    "system-images;android-28;default;x86",
                    "emulator",
                    "platform-tools",
                ],
                env=self.android_env,
                check=True
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Error while installing Android emulator and system image."
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
        print()
        if device is None:
            raise BriefcaseCommandError(
                """\
No Android device was specified. Please specify a specific device on which
to run the app by passing `-d <device_id>`.

"""
                + no_or_wrong_device_message(self.sdk_path)
            )

        # Create an ADB wrapper for the selected device
        adb = self.ADB(sdk_path=self.sdk_path, device=device)

        # Install the latest APK file onto the device.
        print("[{app.app_name}] Installing app (Device ID {device})...".format(
            app=app,
            device=device,
        ))
        adb.install_apk(self.binary_path(app))

        # Compute Android package name based on beeware `bundle` and `app_name`
        # app properties, similar to iOS.
        package = "{app.bundle}.{app.app_name}".format(app=app)

        # We force-stop the app to ensure the activity launches freshly.
        print("[{app.app_name}] Stopping app...".format(app=app))
        adb.force_stop_app(package)

        # To start the app, we launch `org.beeware.android.MainActivity`.
        print("[{app.app_name}] Launching app...".format(app=app))
        adb.start_app(package, "org.beeware.android.MainActivity")


class GradlePackageCommand(GradleMixin, PackageCommand):
    description = "Package an Android APK."


class GradlePublishCommand(GradleMixin, PublishCommand):
    description = "Publish an Android APK."


# Declare the briefcase command bindings
create = GradleCreateCommand  # noqa
update = GradleUpdateCommand  # noqa
build = GradleBuildCommand  # noqa
run = GradleRunCommand  # noqa
package = GradlePackageCommand  # noqa
publish = GradlePublishCommand  # noqa
