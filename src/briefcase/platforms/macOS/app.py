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
from briefcase.platforms.macOS import (
    macOSBuildMixin,
    macOSMixin,
    macOSPackageMixin,
    macOSRunMixin,
    macOSSigningMixin,
)


class macOSAppMixin(macOSMixin):
    output_format = "app"

    def project_path(self, app):
        return self.binary_path(app) / "Contents"

    def binary_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.app"

    def distribution_path(self, app, packaging_format):
        if packaging_format == "dmg":
            return self.platform_path / f"{app.formal_name}-{app.version}.dmg"
        else:
            return self.binary_path(app)

    def entitlements_path(self, app):
        return self.bundle_path(app) / "Entitlements.plist"


class macOSAppCreateCommand(macOSAppMixin, CreateCommand):
    description = "Create and populate a macOS app."


class macOSAppUpdateCommand(macOSAppCreateCommand, UpdateCommand):
    description = "Update an existing macOS app."


class macOSAppOpenCommand(macOSAppMixin, OpenCommand):
    description = "Open the app bundle folder for a macOS app."


class macOSAppBuildCommand(
    macOSAppMixin,
    macOSBuildMixin,
    macOSSigningMixin,
    BuildCommand,
):
    description = "Build a macOS app."

    def build_app(self, app: BaseConfig, test_mode: bool, **kwargs):
        """Build the macOS app.

        :param app: The application to build
        :param test_mode: Should the app be updated in test mode? (default: False)
        """
        self.logger.info("Updating app metadata...", prefix=app.app_name)
        self.update_app_metadata(app=app, test_mode=test_mode)

        # macOS apps don't have anything to compile, but they do need to be
        # signed to be able to execute on M1 hardware - even if it's only an
        # adhoc signing identity. Apply an adhoc signing identity to the
        # app bundle.
        self.logger.info("Adhoc signing app...", prefix=app.app_name)
        self.sign_app(app=app, identity="-")


class macOSAppRunCommand(macOSRunMixin, macOSAppMixin, RunCommand):
    description = "Run a macOS app."


class macOSAppPackageCommand(macOSPackageMixin, macOSAppMixin, PackageCommand):
    description = "Package a macOS app for distribution."


class macOSAppPublishCommand(macOSAppMixin, PublishCommand):
    description = "Publish a macOS app."


# Declare the briefcase command bindings
create = macOSAppCreateCommand  # noqa
update = macOSAppUpdateCommand  # noqa
open = macOSAppOpenCommand  # noqa
build = macOSAppBuildCommand  # noqa
run = macOSAppRunCommand  # noqa
package = macOSAppPackageCommand  # noqa
publish = macOSAppPublishCommand  # noqa
