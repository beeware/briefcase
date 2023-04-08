import datetime
import re
import subprocess
import time
from pathlib import Path
from typing import List

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import BaseConfig, parsed_version
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import AndroidSDK


def safe_formal_name(name):
    """Converts the name into a safe name on Android.

    Certain characters (``/\\:<>"?*|``) can't be used as app names
    on Android; ``!`` causes problems with Android build tooling.
    Also ensure that trailing, leading, and consecutive whitespace
    caused by removing punctuation is collapsed.

    :param name: The candidate name
    :returns: The safe version of the name.
    """
    return re.sub(r"\s+", " ", re.sub(r'[!/\\:<>"\?\*\|]', "", name)).strip()


ANDROID_LOG_PREFIX_REGEX = re.compile(
    r"\d{2}-\d{2} (?P<timestamp>\d{2}:\d{2}:\d{2}.\d{3})\s+\d+\s+\d+ [A-Z] (?P<component>.*?): (?P<content>.*)"
)


def android_log_clean_filter(line):
    """Filter an ADB log to extract the Python-generated message content.

    Any system or stub messages are ignored; all logging prefixes are stripped.
    Python code is identified as coming from the ``python.stdout``

    :param line: The raw line from the system log
    :returns: A tuple, containing (a) the log line, stripped of any system
        logging context, and (b) a boolean indicating if the message should be
        included for analysis purposes (i.e., it's Python content, not a system
        message).
    """
    match = ANDROID_LOG_PREFIX_REGEX.match(line)
    if match:
        groups = match.groupdict()
        include = groups["component"] in {"python.stdout", "python.stderr"}
        return groups["content"], include

    return line, False


class GradleMixin:
    output_format = "gradle"
    platform = "android"

    @property
    def packaging_formats(self):
        return ["aab"]

    @property
    def default_packaging_format(self):
        return "aab"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def project_path(self, app):
        return self.bundle_path(app)

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

    def distribution_path(self, app):
        return self.dist_path / f"{app.formal_name}-{app.version}.aab"

    def run_gradle(self, app, args):
        # Gradle may install the emulator via the dependency chain build-tools > tools >
        # emulator. (The `tools` package only shows up in sdkmanager if you pass
        # `--include_obsolete`.) However, the old sdkmanager built into Android Gradle
        # plugin 4.2 doesn't know about macOS on ARM, so it'll install an x86_64 emulator
        # which won't work with ARM system images.
        #
        # Work around this by pre-installing the emulator with our own sdkmanager before
        # running Gradle. For simplicity, we do this on all platforms, since the user will
        # almost certainly want an emulator soon enough.
        self.tools.android_sdk.verify_emulator()

        gradlew = "gradlew.bat" if self.tools.host_os == "Windows" else "gradlew"
        self.tools.subprocess.run(
            # Windows needs the full path to `gradlew`; macOS & Linux can find it
            # via `./gradlew`. For simplicity of implementation, we always provide
            # the full path.
            [self.bundle_path(app) / gradlew] + args + ["--console", "plain"],
            env=self.tools.android_sdk.env,
            # Set working directory so gradle can use the app bundle path as its
            # project root, i.e., to avoid 'Task assembleDebug not found'.
            cwd=self.bundle_path(app),
            check=True,
        )

    def verify_tools(self):
        """Verify that the Android APK tools in `briefcase` will operate on this system,
        downloading tools as needed."""
        super().verify_tools()
        AndroidSDK.verify(tools=self.tools)
        if not self.is_clone:
            self.logger.add_log_file_extra(self.tools.android_sdk.list_packages)


class GradleCreateCommand(GradleMixin, CreateCommand):
    description = "Create and populate an Android Gradle project."

    def support_package_filename(self, support_revision):
        """The query arguments to use in a support package query request."""
        return (
            f"Python-{self.python_version_tag}-Android-support.b{support_revision}.zip"
        )

    def output_format_template_context(self, app: BaseConfig):
        """Additional template context required by the output format.

        :param app: The config object for the app
        """
        # Android requires an integer "version code". If a version code
        # isn't explicitly provided, generate one from the version number.
        # The build number will also be appended, if provided.
        try:
            version_code = app.version_code
        except AttributeError:
            parsed = parsed_version(app.version)

            v = (list(parsed.release) + [0, 0])[:3]  # version triple
            build = int(getattr(app, "build", "0"))
            version_code = f"{v[0]:d}{v[1]:02d}{v[2]:02d}{build:02d}".lstrip("0")

        return {
            "version_code": version_code,
            "safe_formal_name": safe_formal_name(app.formal_name),
            # Extract test packages, to enable features like test discovery and assertion
            # rewriting.
            "extract_packages": ", ".join(
                f'"{name}"'
                for path in (app.test_sources or [])
                if (name := Path(path).name)
            ),
        }


class GradleUpdateCommand(GradleCreateCommand, UpdateCommand):
    description = "Update an existing Android Gradle project."


class GradleOpenCommand(GradleMixin, OpenCommand):
    description = "Open the folder for an existing Android Gradle project."


class GradleBuildCommand(GradleMixin, BuildCommand):
    description = "Build an Android debug APK."

    def metadata_resource_path(self, app: BaseConfig):
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)
        return self.bundle_path(app) / path_index["metadata_resource_path"]

    def update_app_metadata(self, app: BaseConfig, test_mode: bool):
        with self.input.wait_bar("Setting main module..."):
            with self.metadata_resource_path(app).open("w", encoding="utf-8") as f:
                # Set the name of the app's main module; this will depend
                # on whether we're in test mode.
                f.write(
                    f"""\
<resources>
    <string name="main_module">{app.main_module(test_mode)}</string>
</resources>
"""
                )

    def build_app(self, app: BaseConfig, test_mode: bool, **kwargs):
        """Build an application.

        :param app: The application to build
        :param test_mode: Should the app be updated in test mode? (default: False)
        """
        self.logger.info("Updating app metadata...", prefix=app.app_name)
        self.update_app_metadata(app=app, test_mode=test_mode)

        self.logger.info("Building Android APK...", prefix=app.app_name)
        with self.input.wait_bar("Building..."):
            try:
                self.run_gradle(app, ["assembleDebug"])
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError("Error while building project.") from e


class GradleRunCommand(GradleMixin, RunCommand):
    description = "Run an Android debug APK on a device (physical or virtual)."

    def verify_tools(self):
        super().verify_tools()
        self.tools.android_sdk.verify_emulator()

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
        parser.add_argument(
            "--Xemulator",
            action="append",
            dest="extra_emulator_args",
            help="Additional arguments to use when starting the emulator",
            required=False,
        )
        parser.add_argument(
            "--shutdown-on-exit",
            action="store_true",
            help="Shutdown the emulator on exit.",
            required=False,
        )

    def run_app(
        self,
        app: BaseConfig,
        test_mode: bool,
        passthrough: List[str],
        device_or_avd=None,
        extra_emulator_args=None,
        shutdown_on_exit=False,
        **kwargs,
    ):
        """Start the application.

        :param app: The config object for the app
        :param test_mode: Boolean; Is the app running in test mode?
        :param passthrough: The list of arguments to pass to the app
        :param device_or_avd: The device to target. If ``None``, the user will
            be asked to re-run the command selecting a specific device.
        :param extra_emulator_args: Any additional arguments to pass to the emulator.
        :param shutdown_on_exit: Should the emulator be shut down on exit?
        """
        device, name, avd = self.tools.android_sdk.select_target_device(device_or_avd)

        # If there's no device ID, that means the emulator isn't running.
        # If there's no AVD either, it means the user has chosen to create
        # an entirely new emulator. Create the emulator (if necessary),
        # then start it.
        if device is None:
            if avd is None:
                avd = self.tools.android_sdk.create_emulator()
            else:
                # Ensure the system image for the requested emulator is available.
                # This step is only needed if the AVD already existed; you have to
                # have an image available to create an AVD.
                self.tools.android_sdk.verify_avd(avd)

            if extra_emulator_args:
                extra = f" (with {' '.join(extra_emulator_args)})"
            else:
                extra = ""
            self.logger.info(
                f"Starting emulator {avd}{extra}...",
                prefix=app.app_name,
            )
            device, name = self.tools.android_sdk.start_emulator(
                avd, extra_emulator_args
            )

        try:
            if test_mode:
                label = "test suite"
            else:
                label = "app"

            self.logger.info(
                f"Starting {label} on {name} (device ID {device})", prefix=app.app_name
            )

            # Create an ADB wrapper for the selected device
            adb = self.tools.android_sdk.adb(device=device)

            # Compute Android package name. The Android template uses
            # `package_name` and `module_name`, so we use those here as well.
            package = f"{app.package_name}.{app.module_name}"

            # We force-stop the app to ensure the activity launches freshly.
            self.logger.info("Installing app...", prefix=app.app_name)
            with self.input.wait_bar("Stopping old versions of the app..."):
                adb.force_stop_app(package)

            # Install the latest APK file onto the device.
            with self.input.wait_bar("Installing new app version..."):
                adb.install_apk(self.binary_path(app))

            # To start the app, we launch `org.beeware.android.MainActivity`.
            with self.input.wait_bar(f"Launching {label}..."):
                # Any log after this point must be associated with the new instance
                start_time = datetime.datetime.now()
                adb.start_app(package, "org.beeware.android.MainActivity", passthrough)
                pid = None
                attempts = 0
                delay = 0.01

                # Try to get the PID for 5 seconds.
                fail_time = start_time + datetime.timedelta(seconds=5)
                while not pid and datetime.datetime.now() < fail_time:
                    # Try to get the PID; run in quiet mode because we may
                    # need to do this a lot in the next 5 seconds.
                    pid = adb.pidof(package, quiet=True)
                    if not pid:
                        time.sleep(delay)
                    attempts += 1

            if pid:
                self.logger.info(
                    "Following device log output (type CTRL-C to stop log)...",
                    prefix=app.app_name,
                )
                # Start the app in a way that lets us stream the logs
                log_popen = adb.logcat(pid=pid)

                # Stream the app logs.
                self._stream_app_logs(
                    app,
                    popen=log_popen,
                    test_mode=test_mode,
                    clean_filter=android_log_clean_filter,
                    clean_output=False,
                    # Check for the PID in quiet mode so logs aren't corrupted.
                    stop_func=lambda: not adb.pid_exists(pid=pid, quiet=True),
                    log_stream=True,
                )
            else:
                self.logger.error("Unable to find PID for app", prefix=app.app_name)
                self.logger.error("Logs for launch attempt follow...")

                # Show the log from the start time of the app
                self.logger.error("=" * 75)

                # Pad by a few seconds because the android emulator's clock and the
                # local system clock may not be perfectly aligned.
                adb.logcat_tail(since=start_time - datetime.timedelta(seconds=10))
                raise BriefcaseCommandError(f"Problem starting app {app.app_name!r}")
        finally:
            if shutdown_on_exit:
                with self.tools.input.wait_bar("Stopping emulator..."):
                    adb.kill()


class GradlePackageCommand(GradleMixin, PackageCommand):
    description = "Create an Android App Bundle and APK in release mode."

    def package_app(self, app: BaseConfig, **kwargs):
        """Package the app for distribution.

        This involves building the release app bundle.

        :param app: The application to build
        """
        self.logger.info(
            "Building Android App Bundle and APK in release mode...",
            prefix=app.app_name,
        )
        with self.input.wait_bar("Bundling..."):
            try:
                self.run_gradle(app, ["bundleRelease"])
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError("Error while building project.") from e

        # Move artefact to final location.
        self.tools.shutil.move(
            self.bundle_path(app)
            / "app"
            / "build"
            / "outputs"
            / "bundle"
            / "release"
            / "app-release.aab",
            self.distribution_path(app),
        )


class GradlePublishCommand(GradleMixin, PublishCommand):
    description = "Publish an Android APK."


# Declare the briefcase command bindings
create = GradleCreateCommand
open = GradleOpenCommand
update = GradleUpdateCommand
build = GradleBuildCommand
run = GradleRunCommand
package = GradlePackageCommand
publish = GradlePublishCommand
