import subprocess
from pathlib import Path
from zipfile import ZipFile

from requests import exceptions as requests_exceptions

# "Make adb a function call" should be an `integrations` wrapper like `xcode.py`

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


class ApkMixin:
    output_format = "apk"
    platform = "android"

    @property
    def android_sdk_path_tmp(self):
        # A path in which we prepare the Android SDK.
        return Path.home() / ".briefcase" / "tools" / "android_sdk_tmp"

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

    def verify_tools(self):
        """
        Verify that we're on a Python version where a support package URL is available.
        """
        if self.python_version_tag != "3.7":
            raise BriefcaseCommandError(
                """
Found Python version {self.python_version_tag}. Android packaging currently requires Python 3.7.
        """.format(
                    self=self
                )
            )


# The way to split this up is that you might start with more
# stuff externally specified.


class ApkCreateCommand(ApkMixin, CreateCommand):
    description = "Create and populate an Android APK."

    # TODO: Move these two into my app, and out of this pull request!
    @property
    def support_package_url(self):
        "The URL of the support package to use for apps of this type."
        # Someday this may move into the briefcase-support.org web app, probably
        # around the time we support multiple Python versions.
        return "https://github.com/paulproteus/Python-Android-support/releases/download/v0.5/3.7.zip"

    @property
    def app_template_url(self):
        "The URL for a cookiecutter repository to use when creating apps"
        # Add briefcase.toml to the cookiecutter template
        return "https://github.com/paulproteus/cookiecutter-beeware-android.git"


class ApkUpdateCommand(ApkMixin, UpdateCommand):
    description = "Update an existing Android APK."


class ApkBuildCommand(ApkMixin, BuildCommand):
    description = "Build an Android APK."

    # e.g.
    # mock self.download_url to always download a sentinel zip
    # - validate we create the android_sdk path
    # see xcode tests for mocks of command line tools

    @property
    def android_sdk_url(self):
        """The Android SDK URL appropriate to this operating system."""
        # These URLs have existed since approximately 2017, and they have a built-in autoupdater,
        # so I expect them to keep working for quite a few years longer.
        return "https://dl.google.com/android/repository/sdk-tools-{os}-4333796.zip".format(
            os=self.host_os.lower()
        )

    def verify_tools(self):
        super().verify_tools()

        print()
        print("Ensuring we have the Android SDK...")
        if not self.android_sdk_path.exists():
            try:
                android_sdk_zip_path = self.download_url(
                    url=self.android_sdk_url,
                    download_path=Path.home() / ".briefcase" / "tools",
                )
            except requests_exceptions.ConnectionError:
                raise NetworkFailure("downloading Android SDK")
            with ZipFile(android_sdk_zip_path) as android_sdk_zip:
                android_sdk_zip.extractall(path=self.android_sdk_path_tmp)
            # Remove the ZIP file; it has no purpose now that it is extracted.
            android_sdk_zip_path.unlink()
            # Set executable permissions; Python ZipFile ignores these, but we need them.
            for binpath in (self.android_sdk_path_tmp / "tools" / "bin").glob("*"):
                binpath.chmod(0o755)
            self.android_sdk_path_tmp.rename(self.android_sdk_path)

        print("Ensuring all Android SDK licenses are accepted...")
        self.subprocess.run(
            [self.android_sdk_path / "tools" / "bin" / "sdkmanager", "--licenses"],
            check=True,
            cwd=self.android_sdk_path,
        )

    def build_app(self, app: BaseConfig, **kwargs):
        """
        Build an application.

        :param app: The application to build
        """
        print()
        print("[{app.app_name}] Building Android APK...".format(app=app))

        try:
            print()
            # Use `gradle` to build.
            env = self.os.environ.copy()
            env["ANDROID_SDK_ROOT"] = str(self.android_sdk_path)
            appdir_path = self.bundle_path(app)
            self.subprocess.run(
                [appdir_path / "gradlew", "assembleDebug",],
                env=env,
                check=True,
                cwd=str(appdir_path),
            )

            # Make the binary executable.
            self.os.chmod(str(self.binary_path(app)), 0o755)
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Error while building app {app.app_name}.".format(app=app)
            )


class ApkRunCommand(ApkMixin, RunCommand):
    description = "Run a Linux AppImage."

    def run_app(self, app: BaseConfig, **kwargs):
        """
        Start the application.

        :param app: The config object for the app
        :param base_path: The path to the project directory.
        """
        raise NotImplementedError()
        # TODO: Respect `-d`
        #
        # Find all possible targets:
        # - running devices `adb list-devices`
        # - available emulator devices (`ls ~/.android/emulator`)
        # - mention `briefcase auto-generated device` even if we haven't even created it yet
        #
        # Show all possible targets
        #
        # If you picked an emulator device but it's not started, start it
        #
        # If you picked the briefcase auto-generated device, then create it :)


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
