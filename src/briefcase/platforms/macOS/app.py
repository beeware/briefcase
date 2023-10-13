from __future__ import annotations

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
from briefcase.platforms.macOS import (
    macOSInstallMixin,
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


class macOSAppCreateCommand(macOSAppMixin, macOSInstallMixin, CreateCommand):
    description = "Create and populate a macOS app."

    def support_path(self, app: AppConfig, runtime=False) -> Path:
        if runtime:
            return super().support_path(app)
        else:
            return self.bundle_path(app) / "support"

    def install_app_support_package(self, app: AppConfig):
        """Install the application support package.

        :param app: The config object for the app
        """
        super().install_app_support_package(app)

        # Copy the stdlib into its final location
        with self.input.wait_bar("Copying standard library into app bundle..."):
            runtime_support_path = self.support_path(app, runtime=True)
            if runtime_support_path.is_dir():
                self.tools.shutil.rmtree(runtime_support_path)
            runtime_support_path.mkdir()

            self.tools.shutil.copytree(
                self.support_path(app) / "python-stdlib",
                runtime_support_path / "python-stdlib",
            )

        if not getattr(app, "universal_build", True):
            with self.input.wait_bar("Ensuring stub binary is thin..."):
                # The stub binary is universal by default. If we're building a non-universal app,
                # we can strip the binary to remove the unused slice.
                self.ensure_thin_binary(
                    self.binary_path(app) / "Contents" / "MacOS" / app.formal_name,
                    arch=self.tools.host_arch,
                )


class macOSAppUpdateCommand(macOSAppCreateCommand, UpdateCommand):
    description = "Update an existing macOS app."


class macOSAppOpenCommand(macOSAppMixin, OpenCommand):
    description = "Open the app bundle folder for an existing macOS app."


class macOSAppBuildCommand(macOSAppMixin, macOSSigningMixin, BuildCommand):
    description = "Build a macOS app."

    def build_app(self, app: AppConfig, **kwargs):
        """Build the macOS app.

        :param app: The application to build
        """
        # macOS apps don't have anything to compile, but they do need to be
        # signed to be able to execute on M1 hardware - even if it's only an
        # ad-hoc signing identity. Apply an ad-hoc signing identity to the
        # app bundle.
        self.logger.info("Ad-hoc signing app...", prefix=app.app_name)
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
