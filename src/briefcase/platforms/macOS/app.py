import tempfile
from pathlib import Path

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.config import BaseConfig
from briefcase.platforms.macOS import macOSMixin, macOSRunMixin, macOSPackageMixin


class macOSAppMixin(macOSMixin):
    output_format = 'app'

    def binary_path(self, app):
        return self.bundle_path(app) / '{app.formal_name}.app'.format(app=app)

    def distribution_path(self, app, packaging_format):
        if packaging_format == 'dmg':
            return self.platform_path / '{app.formal_name}-{app.version}.dmg'.format(
                app=app)
        else:
            return self.binary_path(app)

    def entitlements_path(self, app):
        return (
                self.bundle_path(app)
                / 'Entitlements.plist'
        )


class macOSAppCreateCommand(macOSAppMixin, CreateCommand):
    description = "Create and populate a macOS app."

    def install_app_support_package(self, app: BaseConfig):
        """
        Install the application support package.

        :param app: The config object for the app
        """
        super().install_app_support_package(app)

        # keep only Python lib from support package
        lib_path = str(self.support_path(app).parent / 'Support' / 'Python' / 'Resources' / 'lib')

        with tempfile.TemporaryDirectory() as tmpdir:
            self.shutil.move(lib_path, tmpdir)
            self.shutil.rmtree(str(self.support_path(app)))

            self.os.makedirs(str(Path(lib_path).parent))
            self.shutil.move(str(Path(tmpdir) / 'lib'), lib_path)


class macOSAppUpdateCommand(macOSAppMixin, UpdateCommand):
    description = "Update an existing macOS app."


class macOSAppBuildCommand(macOSAppMixin, BuildCommand):
    description = "Build a macOS app."


class macOSAppRunCommand(macOSRunMixin, macOSAppMixin, RunCommand):
    description = "Run a macOS app."


class macOSAppPackageCommand(macOSPackageMixin, macOSAppMixin, PackageCommand):
    description = "Package a macOS app for distribution."


class macOSAppPublishCommand(macOSAppMixin, PublishCommand):
    description = "Publish a macOS app."


# Declare the briefcase command bindings
create = macOSAppCreateCommand  # noqa
update = macOSAppUpdateCommand  # noqa
build = macOSAppBuildCommand  # noqa
run = macOSAppRunCommand  # noqa
package = macOSAppPackageCommand  # noqa
publish = macOSAppPublishCommand  # noqa
