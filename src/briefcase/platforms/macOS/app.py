import os
import tempfile
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

    def distribution_path(self, app, packaging_format):
        if packaging_format == "dmg":
            return self.platform_path / f"{app.formal_name}-{app.version}.dmg"
        else:
            return self.binary_path(app)

    def entitlements_path(self, app):
        return self.bundle_path(app) / "Entitlements.plist"


class macOSAppCreateCommand(macOSAppMixin, CreateCommand):
    description = "Create and populate a macOS app."

    def install_app_support_package(self, app: BaseConfig):
        """Install the application support package.

        :param app: The config object for the app
        """
        super().install_app_support_package(app)

        # Legacy support for the structure of pre-dynamic loading support packages.
        # Keep only Python lib from the (old) support package. If the lib folder
        # doesn't exist, then it's a new dynamic-loading support package.
        lib_path = (
            self.support_path(app).parent / "Support" / "Python" / "Resources" / "lib"
        )
        if lib_path.exists():
            with tempfile.TemporaryDirectory() as tmpdir:
                # TODO: Py3.8 compatibility; os.fsdecode not required in Py3.9
                self.tools.shutil.move(os.fsdecode(lib_path), os.fsdecode(tmpdir))
                self.tools.shutil.rmtree(self.support_path(app))

                self.tools.os.makedirs(Path(lib_path).parent)
                # TODO: Py3.8 compatibility; os.fsdecode not required in Py3.9
                self.tools.shutil.move(
                    os.fsdecode(Path(tmpdir) / "lib"),
                    os.fsdecode(lib_path),
                )


class macOSAppUpdateCommand(macOSAppCreateCommand, UpdateCommand):
    description = "Update an existing macOS app."


class macOSAppOpenCommand(macOSAppMixin, OpenCommand):
    description = "Open the app bundle folder for a macOS app."


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
create = macOSAppCreateCommand  # noqa
update = macOSAppUpdateCommand  # noqa
open = macOSAppOpenCommand  # noqa
build = macOSAppBuildCommand  # noqa
run = macOSAppRunCommand  # noqa
package = macOSAppPackageCommand  # noqa
publish = macOSAppPublishCommand  # noqa
