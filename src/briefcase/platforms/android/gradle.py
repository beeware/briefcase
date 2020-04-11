import subprocess

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import verify_android_sdk
from briefcase.integrations.java import verify_jdk


class GradleMixin:
    output_format = "gradle"
    platform = "android"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def gradlew_path(self, app):
        gradlew = "gradlew.bat" if self.host_os == "Windows" else "gradlew"
        return self.bundle_path(app) / gradlew

    def verify_python_version(self):
        if self.python_version_tag != "3.7":
            raise BriefcaseCommandError(
                """\
Found Python version {self.python_version_tag}. Android packaging currently
requires Python 3.7.""".format(
                    self=self
                )
            )

    def verify_tools(self):
        """
        Verify that we the Android APK tools in `briefcase` will operate on
        this system, downloading tools as needed.
        """
        super().verify_tools()
        self.verify_python_version()
        self.java_home_path = verify_jdk(self)
        self.android_sdk = verify_android_sdk(self)


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
                env=self.android_sdk.env,
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
        self.android_sdk.verify_emulator()

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
                + self.android_sdk.no_or_wrong_device_message()
            )

        # Create an ADB wrapper for the selected device
        adb = self.android_sdk.adb(self, device=device)

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
