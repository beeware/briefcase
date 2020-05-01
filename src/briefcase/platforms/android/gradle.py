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
            dest="device_or_avd",
            help="The device to target; either a device ID for a physical device, "
                 " or an AVD name ('@emulatorName') ",
            required=False,
        )

    def run_app(self, app: BaseConfig, device_or_avd=None, **kwargs):
        """
        Start the application.

        :param app: The config object for the app
        :param device: The device to target. If ``None``, the user will
            be asked to re-run the command selecting a specific device.
        """
        device, name, avd = self.android_sdk.select_target_device(
            device_or_avd=device_or_avd
        )

        # If there's no device ID, that means the emulator isn't running.
        # If there's no AVD either, it means the user has chosen to create
        # an entirely new emulator. Create the emulator (if necessary),
        # then start it.
        if device is None:
            if avd is None:
                avd = self.android_sdk.create_emulator()

            device, name = self.android_sdk.start_emulator(avd)

        print()
        print(
            "[{app.app_name}] Starting app on {name} (device ID {device})".format(
                app=app,
                name=name,
                device=device,
            )
        )

        # Create an ADB wrapper for the selected device
        adb = self.android_sdk.adb(device=device)

        # Compute Android package name based on beeware `bundle` and `app_name`
        # app properties, similar to iOS.
        package = "{app.bundle}.{app.app_name}".format(app=app)

        # We force-stop the app to ensure the activity launches freshly.
        print()
        print("[{app.app_name}] Stopping old versions of the app...".format(app=app))
        adb.force_stop_app(package)

        # Install the latest APK file onto the device.
        print()
        print("[{app.app_name}] Installing app...".format(
            app=app,
        ))
        adb.install_apk(self.binary_path(app))

        # To start the app, we launch `org.beeware.android.MainActivity`.
        print()
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
