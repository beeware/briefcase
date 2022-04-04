import subprocess

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.config import BaseConfig, parsed_version
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import AndroidSDK


class GradleMixin:
    output_format = "gradle"
    platform = "android"

    @property
    def packaging_formats(self):
        return ['aab']

    @property
    def default_packaging_format(self):
        return 'aab'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def binary_path(self, app):
        return (
            self.bundle_path(app)
            / "app"
            / "build"
            / "outputs"
            / "apk"
            / "debug"
            / "app-debug.apk"
        )

    def distribution_path(self, app, packaging_format):
        return (
            self.bundle_path(app)
            / "app"
            / "build"
            / "outputs"
            / "bundle"
            / "release"
            / "app-release.aab"
        )

    def gradlew_path(self, app):
        gradlew = "gradlew.bat" if self.host_os == "Windows" else "gradlew"
        return self.bundle_path(app) / gradlew

    def verify_tools(self):
        """
        Verify that we the Android APK tools in `briefcase` will operate on
        this system, downloading tools as needed.
        """
        super().verify_tools()
        self.android_sdk = AndroidSDK.verify(self)


class GradleCreateCommand(GradleMixin, CreateCommand):
    description = "Create and populate an Android APK."

    def output_format_template_context(self, app: BaseConfig):
        """
        Additional template context required by the output format.

        :param app: The config object for the app
        """
        # Android requires an integer "version code". If a version code
        # isn't explicitly provided, generate one from the version number.
        # The build number will also be appended, if provided.
        try:
            version_code = app.version_code
        except AttributeError:
            parsed = parsed_version(app.version)

            version_triple = (list(parsed.release) + [0, 0])[:3]
            version_code = '{v[0]:d}{v[1]:02d}{v[2]:02d}{build:02d}'.format(
                v=version_triple,
                build=int(getattr(app, 'build', '0'))
            ).lstrip('0')

        return {
            'version_code': version_code,
        }


class GradleUpdateCommand(GradleMixin, UpdateCommand):
    description = "Update an existing Android debug APK."


class GradleBuildCommand(GradleMixin, BuildCommand):
    description = "Build an Android debug APK."

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
                [self.gradlew_path(app), "assembleDebug"],
                env=self.android_sdk.env,
                # Set working directory so gradle can use the app bundle path as its
                # project root, i.e., to avoid 'Task assembleDebug not found'.
                cwd=self.bundle_path(app),
                check=True
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError("Error while building project.")


class GradleRunCommand(GradleMixin, RunCommand):
    description = "Run an Android debug APK on a device (physical or virtual)."

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

        # Compute Android package name. The Android template uses
        # `package_name` and `module_name`, so we use those here as well.
        package = "{app.package_name}.{app.module_name}".format(app=app)

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

        print()
        print("[{app.app_name}] Clearing device log...".format(
            app=app,
        ))
        adb.clear_log()

        # To start the app, we launch `org.beeware.android.MainActivity`.
        print()
        print("[{app.app_name}] Launching app...".format(app=app))
        adb.start_app(package, "org.beeware.android.MainActivity")

        print()
        print("[{app.app_name}] Following device log output (type CTRL-C to stop log)...".format(app=app))
        print("=" * 75)
        adb.logcat()


class GradlePackageCommand(GradleMixin, PackageCommand):
    description = "Create an Android App Bundle and APK in release mode."

    def package_app(self, app: BaseConfig, **kwargs):
        """
        Package the app for distribution.

        This involves building the release app bundle.

        :param app: The application to build
        """
        print("[{app.app_name}] Building Android App Bundle and APK in release mode...".format(app=app))
        try:
            self.subprocess.run(
                # Windows needs the full path to `gradlew`; macOS & Linux can find it
                # via `./gradlew`. For simplicity of implementation, we always provide
                # the full path.
                [self.gradlew_path(app), "bundleRelease"],
                env=self.android_sdk.env,
                # Set working directory so gradle can use the app bundle path as its
                # project root, i.e., to avoid 'Task bundleRelease not found'.
                cwd=self.bundle_path(app),
                check=True
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError("Error while building project.")


class GradlePublishCommand(GradleMixin, PublishCommand):
    description = "Publish an Android APK."


# Declare the briefcase command bindings
create = GradleCreateCommand  # noqa
update = GradleUpdateCommand  # noqa
build = GradleBuildCommand  # noqa
run = GradleRunCommand  # noqa
package = GradlePackageCommand  # noqa
publish = GradlePublishCommand  # noqa
