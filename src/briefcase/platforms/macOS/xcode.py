import subprocess

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import Xcode
from briefcase.platforms.macOS import (
    macOSInstallMixin,
    macOSMixin,
    macOSPackageMixin,
    macOSRunMixin,
)
from briefcase.platforms.macOS.filters import XcodeBuildFilter


class macOSXcodeMixin(macOSMixin):
    output_format = "Xcode"
    supported_host_os_reason = (
        "macOS applications require the Xcode command line "
        "tools, which are only available on macOS."
    )

    def verify_tools(self):
        Xcode.verify(self.tools, min_version=(13, 0, 0))

        # Verify superclass tools *after* xcode. This ensures we get the
        # git check *after* the xcode check.
        super().verify_tools()

    def project_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.xcodeproj"

    def binary_path(self, app):
        return self.bundle_path(app) / "build" / "Release" / f"{app.formal_name}.app"


class macOSXcodeCreateCommand(macOSXcodeMixin, macOSInstallMixin, CreateCommand):
    description = "Create and populate a macOS Xcode project."


class macOSXcodeOpenCommand(macOSXcodeMixin, OpenCommand):
    description = "Open an existing macOS Xcode project."


class macOSXcodeUpdateCommand(macOSXcodeCreateCommand, UpdateCommand):
    description = "Update an existing macOS Xcode project."


class macOSXcodeBuildCommand(macOSXcodeMixin, BuildCommand):
    description = "Build a macOS Xcode project."

    def build_app(self, app: BaseConfig, **kwargs):
        """Build the Xcode project for the application.

        :param app: The application to build
        """
        self.logger.info("Building Xcode project...", prefix=app.app_name)
        with self.input.wait_bar("Building..."):
            try:
                self.tools.subprocess.run(
                    [
                        "xcodebuild",
                        "-project",
                        self.project_path(app),
                        "-verbose" if self.tools.logger.is_deep_debug else "-quiet",
                        "-configuration",
                        "Release",
                        "build",
                    ],
                    check=True,
                    filter_func=(
                        None if self.tools.logger.is_deep_debug else XcodeBuildFilter()
                    ),
                )
                self.logger.info("Build succeeded.")
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to build app {app.app_name}."
                ) from e


class macOSXcodeRunCommand(macOSRunMixin, macOSXcodeMixin, RunCommand):
    description = "Run a macOS app."


class macOSXcodePackageCommand(macOSPackageMixin, macOSXcodeMixin, PackageCommand):
    description = "Package a macOS app for distribution."


class macOSXcodePublishCommand(macOSXcodeMixin, PublishCommand):
    description = "Publish a macOS app."


# Declare the briefcase command bindings
create = macOSXcodeCreateCommand
update = macOSXcodeUpdateCommand
open = macOSXcodeOpenCommand
build = macOSXcodeBuildCommand
run = macOSXcodeRunCommand
package = macOSXcodePackageCommand
publish = macOSXcodePublishCommand
