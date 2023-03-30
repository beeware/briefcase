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


class macOSAppCreateCommand(macOSAppMixin, CreateCommand):
    description = "Create and populate a macOS app."


class macOSAppUpdateCommand(macOSAppCreateCommand, UpdateCommand):
    description = "Update an existing macOS app."


class macOSAppOpenCommand(macOSAppMixin, OpenCommand):
    description = "Open the app bundle folder for an existing macOS app."


class macOSAppBuildCommand(macOSAppMixin, macOSSigningMixin, BuildCommand):
    description = "Build a macOS app."

    def build_app(self, app: BaseConfig, **kwargs):
        """Build the macOS app.

        :param app: The application to build
        """
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
create = macOSAppCreateCommand
update = macOSAppUpdateCommand
open = macOSAppOpenCommand
build = macOSAppBuildCommand
run = macOSAppRunCommand
package = macOSAppPackageCommand
publish = macOSAppPublishCommand
