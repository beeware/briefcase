from __future__ import annotations

import contextlib
import datetime
import re
import subprocess
import time
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import AppConfig
from briefcase.console import ANSI_ESC_SEQ_RE_DEF
from briefcase.debuggers.base import (
    AppPackagesPathMappings,
    DebuggerConnectionMode,
)
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import ADB, AndroidSDK
from briefcase.integrations.subprocess import SubprocessArgT


@dataclass
class AndroidSigningConfig:
    """Signing configuration for an Android release artefact."""

    keystore_path: Path
    alias: str
    store_password: str
    key_password: str


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


# Matches zero or more ANSI control chars wrapping the message for when
# the Android emulator is printing in color.
ANDROID_LOG_PREFIX_REGEX = re.compile(
    rf"(?:{ANSI_ESC_SEQ_RE_DEF})*[A-Z]/(?P<tag>.*?):"
    rf" (?P<content>.*?(?=\x1B|$))(?:{ANSI_ESC_SEQ_RE_DEF})*"
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
        include = groups["tag"] in {"python.stdout", "python.stderr"}
        return groups["content"], include

    return line, False


class GradleMixin:
    output_format = "gradle"
    platform = "android"
    platform_target_version = "0.3.27"

    @property
    def packaging_formats(self):
        return ["aab", "apk", "debug-apk"]

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
        extension = {
            "aab": "aab",
            "apk": "apk",
            "debug-apk": "debug.apk",
        }[app.packaging_format]
        return self.dist_path / f"{app.formal_name}-{app.version}.{extension}"

    def run_gradle(self, app, args: list[SubprocessArgT]):
        # Gradle may install the emulator via the dependency chain build-tools > tools >
        # emulator. (The `tools` package only shows up in sdkmanager if you pass
        # `--include_obsolete`.) However, the old sdkmanager built into Android Gradle
        # plugin 4.2 doesn't know about macOS on ARM, so it'll install an x86_64
        # emulator which won't work with ARM system images.
        #
        # Work around this by pre-installing the emulator with our own sdkmanager before
        # running Gradle. For simplicity, we do this on all platforms, since the user
        # will almost certainly want an emulator soon enough.
        self.tools.android_sdk.verify_emulator()

        gradlew = "gradlew.bat" if self.tools.host_os == "Windows" else "gradlew"
        self.tools.subprocess.run(
            # Windows needs the full path to `gradlew`; macOS & Linux can find it
            # via `./gradlew`. For simplicity of implementation, we always provide
            # the full path.
            [
                self.bundle_path(app) / gradlew,
                "--console",
                "plain",
            ]
            + (["--debug"] if self.tools.console.is_deep_debug else [])
            + args,
            env=self.tools.android_sdk.env,
            # Set working directory so gradle can use the app bundle path as its
            # project root, i.e., to avoid 'Task assembleDebug not found'.
            cwd=self.bundle_path(app),
            check=True,
            # Gradle writes to stdout using the system encoding. So, explicitly use it
            # here to avoid defaulting to the console encoding for the subprocess call.
            # This is mostly for the benefit of Windows where the system encoding may
            # not be the same as the console encoding and typically neither are UTF-8.
            # See #1425 for details.
            encoding=self.tools.system_encoding,
        )

    def verify_tools(self):
        """Verify that the Android APK tools in `briefcase` will operate on this system,
        downloading tools as needed."""
        super().verify_tools()
        AndroidSDK.verify(tools=self.tools)
        if not self.is_clone:
            self.console.add_log_file_extra(self.tools.android_sdk.list_packages)


class GradleCreateCommand(GradleMixin, CreateCommand):
    description = "Create and populate an Android Gradle project."
    hidden_app_properties: Collection[str] = {"permission", "feature"}

    def support_package_filename(self, support_revision):
        """The query arguments to use in a support package query request."""
        return (
            f"Python-{self.python_version_tag}-Android-support.b{support_revision}.zip"
        )

    def output_format_template_context(self, app: AppConfig):
        """Additional template context required by the output format.

        :param app: The config object for the app
        """
        # Android requires an integer "version code". If a version code
        # isn't explicitly provided, generate one from the version number.
        # The build number will also be appended, if provided.
        try:
            version_code = app.version_code
        except AttributeError:
            v = ([*app.version.release, 0, 0])[:3]  # version triple
            build = int(getattr(app, "build", "0"))
            version_code = f"{v[0]:d}{v[1]:02d}{v[2]:02d}{build:02d}".lstrip("0")

        # The default runtime libraries included in an app. The default value is the
        # list that was hard-coded in the Briefcase 0.3.16 Android template, prior to
        # the introduction of customizable system requirements for Android.
        try:
            dependencies = app.build_gradle_dependencies
        except AttributeError:
            self.console.warning("""
*************************************************************************
** WARNING: App does not define build_gradle_dependencies              **
*************************************************************************

    The Android configuration for this app does not contain a
    `build_gradle_dependencies` definition. Briefcase will use a default
    value of:

        build_gradle_dependencies = [
            "androidx.appcompat:appcompat:1.0.2",
            "androidx.constraintlayout:constraintlayout:1.1.3",
            "androidx.swiperefreshlayout:swiperefreshlayout:1.1.0",
        ]

    You should add this definition to the Android configuration
    of your project's pyproject.toml file. See:

        https://briefcase.readthedocs.io/en/stable/reference/platforms/android/gradle.html#build-gradle-dependencies

    for more information.

*************************************************************************

""")
            dependencies = [
                "androidx.appcompat:appcompat:1.0.2",
                "androidx.constraintlayout:constraintlayout:1.1.3",
                "androidx.swiperefreshlayout:swiperefreshlayout:1.1.0",
            ]

        return {
            "version_code": version_code,
            "safe_formal_name": safe_formal_name(app.formal_name),
            "build_gradle_dependencies": {"implementation": dependencies},
        }

    def permissions_context(self, app: AppConfig, x_permissions: dict[str, str]):
        """Additional template context for permissions.

        :param app: The config object for the app
        :param x_permissions: The dictionary of known cross-platform permission
            definitions.
        :returns: The template context describing permissions for the app.
        """
        # Default permissions for all Android apps
        permissions = {
            "android.permission.INTERNET": {},
            "android.permission.ACCESS_NETWORK_STATE": {},
        }

        # Default feature usage for all Android apps
        features = {}

        if x_permissions["bluetooth"]:
            permissions["android.permission.ACCESS_COARSE_LOCATION"] = {
                "android:maxSdkVersion": "30"
            }
            permissions["android.permission.ACCESS_FINE_LOCATION"] = {
                "android:maxSdkVersion": "30"
            }
            permissions["android.permission.BLUETOOTH"] = {
                "android:maxSdkVersion": "30"
            }
            permissions["android.permission.BLUETOOTH_ADMIN"] = {
                "android:maxSdkVersion": "30"
            }
            permissions["android.permission.BLUETOOTH_CONNECT"] = {}
            permissions["android.permission.BLUETOOTH_SCAN"] = {
                "android:usesPermissionFlags": "neverForLocation"
            }

        if x_permissions["camera"]:
            permissions["android.permission.CAMERA"] = {}
            features["android.hardware.camera"] = False
            features["android.hardware.camera.any"] = False
            features["android.hardware.camera.front"] = False
            features["android.hardware.camera.external"] = False
            features["android.hardware.camera.autofocus"] = False

        if x_permissions["microphone"]:
            permissions["android.permission.RECORD_AUDIO"] = {}

        if x_permissions["fine_location"]:
            permissions["android.permission.ACCESS_FINE_LOCATION"] = {}
            features["android.hardware.location.network"] = False
            features["android.hardware.location.gps"] = False
            # We're good with the location. So we can also use BLUETOOTH_SCAN.
            bt_scan_perm = permissions.get("android.permission.BLUETOOTH_SCAN")
            if bt_scan_perm:
                bt_scan_perm.pop("android:usesPermissionFlags", None)

        if x_permissions["coarse_location"]:
            permissions["android.permission.ACCESS_COARSE_LOCATION"] = {}
            features["android.hardware.location.network"] = False
            features["android.hardware.location.gps"] = False
            # We're good with the location. So we can also use BLUETOOTH_SCAN.
            bt_scan_perm = permissions.get("android.permission.BLUETOOTH_SCAN")
            if bt_scan_perm:
                bt_scan_perm.pop("android:usesPermissionFlags", None)

        if x_permissions["background_location"]:
            permissions["android.permission.ACCESS_BACKGROUND_LOCATION"] = {}
            features["android.hardware.location.network"] = False
            features["android.hardware.location.gps"] = False

        if x_permissions["photo_library"]:
            permissions["android.permission.READ_MEDIA_VISUAL_USER_SELECTED"] = {}

        # Override any permission and entitlement definitions
        # with the platform-specific definitions
        permissions.update(app.permission)
        features.update(getattr(app, "feature", {}))

        return {
            "permissions": permissions,
            "features": features,
        }


class GradleUpdateCommand(GradleCreateCommand, UpdateCommand):
    description = "Update an existing Android Gradle project."
    supports_debugger = True


class GradleOpenCommand(GradleMixin, OpenCommand):
    description = "Open the folder for an existing Android Gradle project."


class GradleBuildCommand(GradleMixin, BuildCommand):
    description = "Build an Android debug APK."
    supports_debugger = True

    def metadata_resource_path(self, app: AppConfig):
        return self.bundle_path(app) / self.path_index(app, "metadata_resource_path")

    def extract_packages_path(self, app: AppConfig):
        return self.bundle_path(app) / self.path_index(app, "extract_packages_path")

    def update_app_metadata(self, app: AppConfig):
        with (
            self.console.wait_bar("Setting main module..."),
            self.metadata_resource_path(app).open("w", encoding="utf-8") as f,
        ):
            # Set the name of the app's main module; this will depend
            # on whether we're in test mode.
            f.write(f"""\
<resources>
    <string name="main_module">{app.main_module()}</string>
</resources>
""")

        with (
            self.console.wait_bar("Setting packages to extract..."),
            self.extract_packages_path(app).open("w", encoding="utf-8") as f,
        ):
            if app.debugger:
                # In debug mode include the .py files and extract all of them so
                # that the debugger can get the source code at runtime. This is
                # e.g. necessary for setting breakpoints in VS Code.
                extract_packages = ["*"]
            else:
                # Extract test packages, to enable features like test discovery and
                # assertion rewriting.
                extract_sources = app.test_sources or []
                extract_packages = [
                    name for path in extract_sources if (name := Path(path).name)
                ]

            f.write("\n".join(extract_packages))

    def build_app(self, app: AppConfig, **kwargs):
        """Build an application.

        :param app: The application to build
        """
        self.console.info("Updating app metadata...", prefix=app.app_name)
        self.update_app_metadata(app=app)

        self.console.info("Building Android APK...", prefix=app.app_name)
        with self.console.wait_bar("Building..."):
            try:
                self.run_gradle(app, ["assembleDebug"])
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError("Error while building project.") from e


class GradleRunCommand(GradleMixin, RunCommand):
    description = "Run an Android debug APK on a device (physical or virtual)."
    supports_debugger = True

    def verify_tools(self):
        super().verify_tools()
        self.tools.android_sdk.verify_emulator()

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "-d",
            "--device",
            dest="device_or_avd",
            help=(
                "The device to target; either a device ID for a physical device, "
                " or an AVD name ('@emulatorName') "
            ),
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
            help="Shutdown the emulator on exit",
            required=False,
        )
        parser.add_argument(
            "--revoke-permission",
            metavar="PERMISSION",
            action="append",
            dest="revoke_permissions",
            help="Revoke specified permission before launching the app",
            required=False,
        )
        parser.add_argument(
            "--forward-port",
            action="append",
            dest="forward_ports",
            type=int,
            help="Forward the specified port from host to device.",
        )
        parser.add_argument(
            "--reverse-port",
            action="append",
            dest="reverse_ports",
            type=int,
            help="Reverse the specified port from device to host.",
        )

    def debugger_app_packages_path_mapping(
        self, app: AppConfig
    ) -> AppPackagesPathMappings:
        """Get the path mappings for the app packages.

        :param app: The config object for the app
        :returns: The path mappings for the app packages
        """
        app_packages_path = self.bundle_path(app) / "app/build/python/pip/debug/common"
        return AppPackagesPathMappings(
            sys_path_regex="requirements$",
            host_folder=f"{app_packages_path}",
        )

    def run_app(
        self,
        app: AppConfig,
        passthrough: list[str],
        device_or_avd=None,
        extra_emulator_args=None,
        shutdown_on_exit=False,
        revoke_permissions: list[str] | None = None,
        forward_ports: list[int] | None = None,
        reverse_ports: list[int] | None = None,
        **kwargs,
    ):
        """Start the application.

        :param app: The config object for the app
        :param passthrough: The list of arguments to pass to the app
        :param device_or_avd: The device to target. If ``None``, the user will
            be asked to re-run the command selecting a specific device.
        :param extra_emulator_args: Any additional arguments to pass to the emulator.
        :param shutdown_on_exit: Should the emulator be shut down on exit?
        :param revoke_permissions: A list of permissions to revoke before launching
            the app.
        :param forward_ports: A list of ports to forward for the app.
        :param reverse_ports: A list of ports to reversed for the app.
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
            self.console.info(f"Starting emulator {avd}{extra}...", prefix=app.app_name)
            device, name = self.tools.android_sdk.start_emulator(
                avd, extra_emulator_args
            )

        try:
            label = "test suite" if app.test_mode else "app"

            self.console.info(
                f"Starting {label} on {name} (device ID {device})", prefix=app.app_name
            )

            # Create an ADB wrapper for the selected device
            adb = self.tools.android_sdk.adb(device=device)

            # Compute Android package name. The Android template uses
            # `package_name` and `module_name`, so we use those here as well.
            package = f"{app.package_name}.{app.module_name}"

            # We force-stop the app to ensure the activity launches freshly.
            self.console.info("Installing app...", prefix=app.app_name)
            with self.console.wait_bar("Stopping old versions of the app..."):
                adb.force_stop_app(package)

            # Install the latest APK file onto the device.
            with self.console.wait_bar("Installing new app version..."):
                adb.install_apk(self.binary_path(app))

            if revoke_permissions:
                # Revoke specified app permissions to ensure a reproducible
                # starting state.
                with self.console.wait_bar("Revoking app permissions..."):
                    for permission in revoke_permissions:
                        self.console.info(
                            f"Revoking permission: {permission}", prefix=app.app_name
                        )
                        adb.revoke_permission(package, permission)

            forward_ports = forward_ports or []
            reverse_ports = reverse_ports or []

            env = {}
            if self.console.is_debug:
                env["BRIEFCASE_DEBUG"] = "1"

            if app.debugger:
                env["BRIEFCASE_DEBUGGER"] = app.debugger.get_env_config(self, app)
                if app.debugger.connection_mode == DebuggerConnectionMode.SERVER:
                    forward_ports.append(app.debugger_port)
                else:
                    reverse_ports.append(app.debugger_port)

            # Forward/Reverse requested ports
            with self.forward_ports(adb, forward_ports, reverse_ports):
                # To start the app, we launch `org.beeware.android.MainActivity`.
                with self.console.wait_bar(f"Launching {label}..."):
                    # capture the earliest time for device logging in case PID not found
                    device_start_time = adb.datetime()

                    adb.start_app(
                        package, "org.beeware.android.MainActivity", passthrough, env
                    )

                    # Try to get the PID for 5 seconds.
                    pid = None
                    fail_time = datetime.datetime.now() + datetime.timedelta(seconds=5)
                    while not pid and datetime.datetime.now() < fail_time:
                        # Try to get the PID; run in quiet mode because we may
                        # need to do this a lot in the next 5 seconds.
                        pid = adb.pidof(package, quiet=2)
                        if not pid:
                            time.sleep(0.01)

                if pid:
                    self.console.info(
                        "Following device log output (type CTRL-C to stop log)...",
                        prefix=app.app_name,
                    )
                    # Start adb's logcat in a way that lets us stream the logs
                    log_popen = adb.logcat(pid=pid)

                    # Stream the app logs.
                    self._stream_app_logs(
                        app,
                        popen=log_popen,
                        clean_filter=android_log_clean_filter,
                        clean_output=False,
                        # Check for the PID in quiet mode so logs aren't corrupted.
                        stop_func=lambda: not adb.pid_exists(pid=pid, quiet=2),
                        log_stream=True,
                    )
                else:
                    self.console.error(
                        "Unable to find PID for app", prefix=app.app_name
                    )
                    self.console.error("Logs for launch attempt follow...")
                    self.console.error("=" * 75)

                    # Show the log from the start time of the app
                    adb.logcat_tail(since=device_start_time)

                    raise BriefcaseCommandError(
                        f"Problem starting app {app.app_name!r}"
                    )

        finally:
            if shutdown_on_exit:
                with self.tools.console.wait_bar("Stopping emulator..."):
                    adb.kill()

    @contextlib.contextmanager
    def forward_ports(
        self, adb: ADB, forward_ports: list[int], reverse_ports: list[int]
    ):
        """Establish a port forwarding/reversion.

        :param adb: The ADB wrapper for the device
        :param forward_ports: Ports to forward via ADB
        :param reverse_ports: Ports to reverse via ADB
        """
        for port in forward_ports:
            adb.forward(port, port)
        for port in reverse_ports:
            adb.reverse(port, port)

        yield

        for port in forward_ports:
            adb.forward_remove(port)
        for port in reverse_ports:
            adb.reverse_remove(port)


class GradlePackageCommand(GradleMixin, PackageCommand):
    description = "Create a release artefact from an Android Gradle project."

    ADHOC_SIGN_HELP = "Create an unsigned release artefact"
    IDENTITY_HELP = "The path to a .jks keystore file to use for signing"

    def add_options(self, parser):
        super().add_options(parser)

        parser.add_argument(
            "--keystore-alias",
            dest="keystore_alias",
            help="The alias of the signing key in the keystore",
            required=False,
        )
        parser.add_argument(
            "--keystore-password",
            dest="keystore_password",
            help="The password for the keystore",
            required=False,
        )
        parser.add_argument(
            "--key-password",
            dest="key_password",
            help=(
                "The password for the signing key "
                "(defaults to the keystore password if not specified)"
            ),
            required=False,
        )

    @property
    def _keytool(self) -> Path:
        """Path to the keytool executable bundled with the JDK."""
        ext = ".exe" if self.tools.host_os == "Windows" else ""
        return self.tools.java.java_home / "bin" / f"keytool{ext}"

    def _keystore_candidates(self) -> list[Path]:
        """Find candidate .jks keystore files in standard locations.

        Searches the project folder, its .android subfolder, and ~/.android.
        """
        search_paths = [
            self.base_path,
            self.base_path / ".android",
            self.tools.home_path / ".android",
        ]
        candidates = []
        for search_path in search_paths:
            if search_path.is_dir():
                candidates.extend(sorted(search_path.glob("*.jks")))
        return sorted(set(candidates))

    def create_keystore(
        self,
        app: AppConfig,
        keystore_alias: str | None = None,
        store_password: str | None = None,
        key_password: str | None = None,
    ) -> AndroidSigningConfig:
        """Create a new keystore for signing Android apps.

        The keystore is created at <base_path>/.android/<bundle_identifier>.jks.

        :param app: The app being packaged
        :param keystore_alias: The key alias; prompted if not provided
        :param store_password: The keystore password; prompted if not provided
        :param key_password: The key password; defaults to store_password
        :returns: An AndroidSigningConfig for the new keystore
        """
        keystore_path = self.base_path / ".android" / f"{app.bundle_identifier}.jks"

        if keystore_alias is None:
            keystore_alias = self.console.text_question(
                description="Key alias",
                intro="Enter an alias for the signing key.",
                default=app.app_name,
            )

        if store_password is None:
            store_password = self.console.password_question(
                description="Keystore password",
                intro="Enter a password for the keystore.",
            )

        if key_password is None:
            key_password = self.console.password_question(
                description="Key password",
                intro="Enter a password for the signing key.",
                default=store_password,
            )

        keystore_path.parent.mkdir(parents=True, exist_ok=True)

        with self.console.wait_bar("Creating keystore..."):
            try:
                self.tools.subprocess.run(
                    [
                        self._keytool,
                        "-genkeypair",
                        "-v",
                        "-keystore",
                        str(keystore_path),
                        "-alias",
                        keystore_alias,
                        "-keyalg",
                        "RSA",
                        "-keysize",
                        "2048",
                        "-validity",
                        "10000",
                        "-storepass",
                        store_password,
                        "-keypass",
                        key_password,
                        "-dname",
                        (
                            f"CN={app.formal_name}, "
                            "OU=Unknown, O=Unknown, L=Unknown, ST=Unknown, C=Unknown"
                        ),
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError("Failed to create keystore.") from e

        self.console.info(f"""
A new keystore has been created at:

    {keystore_path}

Keep this file secure and backed up. If you lose it, you will not be able to
publish updates to this app on the Play Store.

In future, you can reuse this keystore by running:

    $ briefcase package android --identity {keystore_path}

""")
        return AndroidSigningConfig(
            keystore_path=keystore_path,
            alias=keystore_alias,
            store_password=store_password,
            key_password=key_password,
        )

    def select_keystore(
        self,
        app: AppConfig,
        identity: str | None = None,
        keystore_alias: str | None = None,
        keystore_password: str | None = None,
        key_password: str | None = None,
    ) -> AndroidSigningConfig:
        """Select or create a keystore for signing.

        If ``identity`` is provided it is treated as a path to a .jks keystore
        file.  Otherwise keystores are discovered from standard locations and
        the user is prompted to select one or create a new one.

        :param app: The app being packaged
        :param identity: Path to a keystore file, or None to discover/create
        :param keystore_alias: The key alias; prompted if not provided
        :param keystore_password: The keystore password; prompted if not provided
        :param key_password: The key password; defaults to keystore_password
        :returns: An AndroidSigningConfig for the selected keystore
        """
        if identity is not None:
            keystore_path = Path(identity)
            if not keystore_path.exists():
                raise BriefcaseCommandError(
                    f"Keystore file {str(identity)!r} does not exist."
                )
        else:
            candidates = self._keystore_candidates()

            _CREATE_NEW = "__create_new__"
            options = {_CREATE_NEW: "Create a new keystore"}
            for path in candidates:
                options[str(path)] = str(path)

            selection = self.console.selection_question(
                description="Keystore",
                intro=("Select the keystore to use for signing, or create a new one."),
                options=options,
            )

            if selection == _CREATE_NEW:
                return self.create_keystore(
                    app,
                    keystore_alias=keystore_alias,
                    store_password=keystore_password,
                    key_password=key_password,
                )

            keystore_path = Path(selection)

        if keystore_alias is None:
            keystore_alias = self.console.text_question(
                description="Key alias",
                intro="Enter the alias of the signing key in the keystore.",
                default=app.app_name,
            )

        if keystore_password is None:
            keystore_password = self.console.password_question(
                description="Keystore password",
                intro="Enter the password for the keystore.",
            )

        if key_password is None:
            key_password = keystore_password

        return AndroidSigningConfig(
            keystore_path=keystore_path,
            alias=keystore_alias,
            store_password=keystore_password,
            key_password=key_password,
        )

    def package_app(
        self,
        app: AppConfig,
        adhoc_sign: bool = False,
        identity: str | None = None,
        keystore_alias: str | None = None,
        keystore_password: str | None = None,
        key_password: str | None = None,
        **kwargs,
    ):
        """Package the app for distribution.

        This involves building the release app bundle.

        :param app: The application to build
        :param adhoc_sign: If True, produce an unsigned artefact
        :param identity: Path to a .jks keystore file
        :param keystore_alias: The alias of the signing key in the keystore
        :param keystore_password: The keystore password
        :param key_password: The key password (defaults to keystore_password)
        """
        self.console.info(
            "Building Android App Bundle and APK in release mode...",
            prefix=app.app_name,
        )

        build_type, build_artefact_path = {
            "aab": ("bundleRelease", "bundle/release/app-release.aab"),
            "apk": ("assembleRelease", "apk/release/app-release-unsigned.apk"),
            "debug-apk": ("assembleDebug", "apk/debug/app-debug.apk"),
        }[app.packaging_format]

        gradle_args = [build_type]

        extra_gradle = getattr(app, "build_gradle_extra_content", "") or ""
        if "signingConfig" in extra_gradle:
            if identity is not None:
                raise BriefcaseCommandError(
                    "Cannot use --identity when build_gradle_extra_content already "
                    "configures signing.\n\n"
                    "Remove the signingConfig block from build_gradle_extra_content "
                    "and use --identity instead, or remove --identity to let the "
                    "existing Gradle signing configuration be used."
                )
            if not adhoc_sign:
                self.console.warning("""
Signing is configured via build_gradle_extra_content in pyproject.toml.
Briefcase will use that signing configuration.

For better security, consider removing the signing block from
build_gradle_extra_content and using briefcase's built-in signing instead:

    $ briefcase package android --identity /path/to/keystore.jks

""")
                adhoc_sign = True

        if app.packaging_format != "debug-apk" and not adhoc_sign:
            signing_config = self.select_keystore(
                app,
                identity=identity,
                keystore_alias=keystore_alias,
                keystore_password=keystore_password,
                key_password=key_password,
            )
            gradle_args += [
                f"-Pandroid.injected.signing.store.file={signing_config.keystore_path!s}",
                f"-Pandroid.injected.signing.store.password={signing_config.store_password}",
                f"-Pandroid.injected.signing.key.alias={signing_config.alias}",
                f"-Pandroid.injected.signing.key.password={signing_config.key_password}",
            ]

        with self.console.wait_bar("Bundling..."):
            try:
                self.run_gradle(app, gradle_args)
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError("Error while building project.") from e

        # Move artefact to final location.
        self.tools.shutil.move(
            self.bundle_path(app) / "app/build/outputs" / build_artefact_path,
            self.distribution_path(app),
        )


class GradlePublishCommand(GradleMixin, PublishCommand):
    description = "Publish an Android Gradle project."


# Declare the briefcase command bindings
create = GradleCreateCommand
open = GradleOpenCommand
update = GradleUpdateCommand
build = GradleBuildCommand
run = GradleRunCommand
package = GradlePackageCommand
publish = GradlePublishCommand
