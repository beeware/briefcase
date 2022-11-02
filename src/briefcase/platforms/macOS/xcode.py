import os
import subprocess
import time
from pathlib import Path

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    TestCommand,
    UpdateCommand,
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError, TestSuiteFailure
from briefcase.integrations.subprocess import json_parser
from briefcase.integrations.xcode import verify_xcode_install
from briefcase.platforms.macOS import macOSMixin, macOSPackageMixin, macOSRunMixin


class macOSXcodeMixin(macOSMixin):
    output_format = "Xcode"

    def verify_tools(self):
        if self.tools.host_os != "Darwin":
            raise BriefcaseCommandError(
                "macOS applications require the Xcode command line tools, "
                "which are only available on macOS."
            )
        # Require XCode 10.0.0. There's no particular reason for this
        # specific version, other than it's a nice round number that's
        # not *that* old at time of writing.
        verify_xcode_install(self.tools, min_version=(10, 0, 0))

        # Verify superclass tools *after* xcode. This ensures we get the
        # git check *after* the xcode check.
        super().verify_tools()

    def project_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.xcodeproj"

    def binary_path(self, app):
        return (
            self.platform_path
            / self.output_format
            / f"{app.formal_name}"
            / "build"
            / "Release"
            / f"{app.formal_name}.app"
        )

    def distribution_path(self, app, packaging_format):
        if packaging_format == "dmg":
            return self.platform_path / f"{app.formal_name}-{app.version}.dmg"
        else:
            return self.binary_path(app)

    def entitlements_path(self, app):
        return (
            self.bundle_path(app)
            / f"{app.formal_name}"
            / f"{app.app_name}.entitlements"
        )


class macOSXcodeCreateCommand(macOSXcodeMixin, CreateCommand):
    description = "Create and populate a macOS Xcode project."


class macOSXcodeOpenCommand(macOSXcodeMixin, OpenCommand):
    description = "Open a macOS Xcode project."


class macOSXcodeUpdateCommand(macOSXcodeCreateCommand, UpdateCommand):
    description = "Update an existing macOS Xcode project."


class macOSXcodeBuildCommand(macOSXcodeMixin, BuildCommand):
    description = "Build a macOS Xcode project."

    def build_app(self, app: BaseConfig, **kwargs):
        """Build the Xcode project for the application.

        :param app: The application to build
        """

        self.logger.info("Building XCode project...", prefix=app.app_name)
        with self.input.wait_bar("Building..."):
            try:
                self.tools.subprocess.run(
                    [
                        "xcodebuild",
                        "-project",
                        self.project_path(app),
                        "-quiet",
                        "-configuration",
                        "Release",
                        "build",
                    ],
                    check=True,
                )
                self.logger.info("Build succeeded.")
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to build app {app.app_name}."
                ) from e


class macOSXcodeTestCommand(macOSXcodeMixin, TestCommand):
    description = "Test an macOS Xcode project."

    def build_path(self, app: BaseConfig):
        """Determine the BUILD_DIR used by the Xcode project for an app.

        **NOTE** This isn't a simple path construction; it requires
        invoking xcodebuild to get a configuration value that is determined
        by Xcode. This means (a) it isn't cheap to compute, so it should be
        cached; and (b) it is possible (although unlikely) for the call to fail.

        :param app: The app whose build path you require.
        """
        project_data = self.tools.subprocess.parse_output(
            json_parser,
            [
                "xcodebuild",
                "-project",
                self.project_path(app),
                "-showBuildSettings",
                "-json",
            ],
        )
        return Path(project_data[0]["buildSettings"]["BUILD_DIR"])

    def test_app(self, app: BaseConfig, **kwargs):
        """Test the Xcode project for the application.

        :param app: The application to test
        """
        self.logger.info("Installing Test code...", prefix=app.app_name)
        self.install_test_code(app=app)

        self.logger.info("Installing Test dependencies...", prefix=app.app_name)
        self.install_test_dependencies(app=app)

        self.logger.info("Building XCode Test project...", prefix=app.app_name)
        with self.input.wait_bar("Building..."):
            try:
                self.tools.subprocess.run(
                    [
                        "xcodebuild",
                        "build-for-testing",
                        "-project",
                        self.project_path(app),
                        "-scheme",
                        app.formal_name,
                        "-configuration",
                        "Debug",
                        "-destination",
                        f"platform=macOS,arch={self.tools.host_arch}",
                        "-quiet",
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to build test app {app.app_name}."
                ) from e

        # Interrogate the project file to get the DerivedData build path
        build_path = self.build_path(app)

        # Start the logger
        try:
            self.logger.info("Starting logger...", prefix=app.app_name)
            log_sender = os.fsdecode(
                build_path
                / "Debug"
                / f"{app.formal_name}.app"
                / "Contents"
                / "MacOS"
                / app.formal_name
            )
            log_popen = self.tools.subprocess.Popen(
                [
                    "log",
                    "stream",
                    "--style",
                    "compact",
                    "--predicate",
                    f'processImagePath=="{log_sender}"',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            )

            # Wait for the log stream start up
            time.sleep(0.25)

            self.logger.info("Testing XCode project...", prefix=app.app_name)
            test_popen = self.tools.subprocess.Popen(
                [
                    "xcodebuild",
                    "test-without-building",
                    "-project",
                    self.project_path(app),
                    "-scheme",
                    app.formal_name,
                    "-configuration",
                    "Debug",
                    "-destination",
                    f"platform=macOS,arch={self.tools.host_arch}",
                    "-quiet",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            )
            # Wait for the test runner to start up
            time.sleep(0.25)

            # Start streaming logs for the test.
            self.logger.info("=" * 75)
            self.tools.subprocess.stream_output(
                "log stream", log_popen, stop_func=lambda: test_popen.poll() is not None
            )
            self.logger.info("=" * 75)

            if test_popen.returncode == 0:
                self.logger.info("Test suite passed!", prefix=app.app_name)
            else:
                self.logger.error("Test suite failed!", prefix=app.app_name)
                raise TestSuiteFailure()
        except KeyboardInterrupt:
            pass  # Catch CTRL-C to exit normally
        finally:
            self.tools.subprocess.cleanup("log stream", log_popen)
            try:
                self.tools.subprocess.cleanup("test runner", test_popen)
            except NameError:
                # Failure occurred before test_popen was created
                pass


class macOSXcodeRunCommand(macOSRunMixin, macOSXcodeMixin, RunCommand):
    description = "Run a macOS app."


class macOSXcodePackageCommand(macOSPackageMixin, macOSXcodeMixin, PackageCommand):
    description = "Package a macOS app for distribution."


class macOSXcodePublishCommand(macOSXcodeMixin, PublishCommand):
    description = "Publish a macOS app."


# Declare the briefcase command bindings
create = macOSXcodeCreateCommand  # noqa
update = macOSXcodeUpdateCommand  # noqa
open = macOSXcodeOpenCommand  # noqa
build = macOSXcodeBuildCommand  # noqa
test = macOSXcodeTestCommand  # noqa
run = macOSXcodeRunCommand  # noqa
package = macOSXcodePackageCommand  # noqa
publish = macOSXcodePublishCommand  # noqa
