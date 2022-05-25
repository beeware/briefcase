import subprocess

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import verify_xcode_install
from briefcase.platforms.macOS import macOSMixin, macOSPackageMixin, macOSRunMixin


class macOSXcodeMixin(macOSMixin):
    output_format = "Xcode"

    def verify_tools(self):
        if self.host_os != "Darwin":
            raise BriefcaseCommandError(
                "macOS applications require the Xcode command line tools, "
                "which are only available on macOS."
            )
        # Require XCode 10.0.0. There's no particular reason for this
        # specific version, other than it's a nice round number that's
        # not *that* old at time of writing.
        verify_xcode_install(self, min_version=(10, 0, 0))

        # Verify superclass tools *after* xcode. This ensures we get the
        # git check *after* the xcode check.
        super().verify_tools()

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


class macOSXcodeUpdateCommand(macOSXcodeMixin, UpdateCommand):
    description = "Update an existing macOS Xcode project."


class macOSXcodeBuildCommand(macOSXcodeMixin, BuildCommand):
    description = "Build a macOS Xcode project."

    def build_app(self, app: BaseConfig, **kwargs):
        """
        Build the Xcode project for the application.

        :param app: The application to build
        """

        self.logger.info()
        self.logger.info(f"[{app.app_name}] Building XCode project...")

        try:
            self.subprocess.run(
                [
                    "xcodebuild",  # ' '.join(build_settings_str),
                    "-project",
                    self.bundle_path(app) / f"{app.formal_name}.xcodeproj",
                    "-quiet",
                    "-configuration",
                    "Release",
                    "build",
                ],
                check=True,
            )
            self.logger.info("Build succeeded.")
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to build app {app.app_name}.") from e


class macOSXcodeRunCommand(macOSRunMixin, macOSXcodeMixin, RunCommand):
    description = "Run a macOS app."


class macOSXcodePackageCommand(macOSPackageMixin, macOSXcodeMixin, PackageCommand):
    description = "Package a macOS app for distribution."


class macOSXcodePublishCommand(macOSXcodeMixin, PublishCommand):
    description = "Publish a macOS app."


# Declare the briefcase command bindings
create = macOSXcodeCreateCommand  # noqa
update = macOSXcodeUpdateCommand  # noqa
build = macOSXcodeBuildCommand  # noqa
run = macOSXcodeRunCommand  # noqa
package = macOSXcodePackageCommand  # noqa
publish = macOSXcodePublishCommand  # noqa
