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
    SigningIdentity,
    macOSCreateMixin,
    macOSMixin,
    macOSPackageMixin,
    macOSRunMixin,
    macOSSigningMixin,
)
from briefcase.platforms.macOS.utils import AppPackagesMergeMixin


class macOSAppMixin(macOSMixin):
    output_format = "app"

    def project_path(self, app):
        return self.binary_path(app) / "Contents"

    def binary_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.app"

    def binary_executable_path(self, app) -> Path:
        # The actual binary in a macOS app is a known path
        # inside the "binary" app bundle that is executed.
        return self.binary_path(app) / "Contents/MacOS" / app.formal_name


class macOSAppCreateCommand(macOSAppMixin, macOSCreateMixin, CreateCommand):
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

    def install_app_resources(self, app: AppConfig):
        super().install_app_resources(app)

        # macOS will cache application icons. Touching the .app folder flushes the icon
        # cache for the app, ensuring the current icon is loaded.
        self.binary_path(app).touch(exist_ok=True)


class macOSAppUpdateCommand(macOSAppCreateCommand, UpdateCommand):
    description = "Update an existing macOS app."


class macOSAppOpenCommand(macOSAppMixin, OpenCommand):
    description = "Open the app bundle folder for an existing macOS app."


class macOSAppBuildCommand(
    macOSAppMixin,
    macOSSigningMixin,
    AppPackagesMergeMixin,
    BuildCommand,
):
    description = "Build a macOS app."

    def build_app(self, app: AppConfig, **kwargs):
        """Build the macOS app.

        :param app: The application to build
        """
        self.logger.info("Building App...", prefix=app.app_name)

        # Move the unbuilt binary in to the final executable location
        unbuilt_path = self.unbuilt_executable_path(app)
        if unbuilt_path.exists():
            with self.input.wait_bar("Renaming stub binary..."):
                unbuilt_path.rename(self.binary_executable_path(app))

        if not getattr(app, "universal_build", True):
            with self.input.wait_bar("Ensuring stub binary is thin..."):
                # The stub binary is universal by default. If we're building a non-universal app,
                # we can strip the binary to remove the unused slice. This occurs before the
                self.ensure_thin_binary(
                    self.binary_executable_path(app),
                    arch=self.tools.host_arch,
                )

        # macOS apps don't have anything to compile, but they do need to be
        # signed to be able to execute on Apple Silicon hardware - even if it's only an
        # ad-hoc signing identity. Apply an ad-hoc signing identity to the
        # app bundle.
        self.logger.info("Ad-hoc signing app...", prefix=app.app_name)
        self.sign_app(app=app, identity=SigningIdentity())


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
