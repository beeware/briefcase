import subprocess

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS import macOSMixin, macOSRunMixin, macOSPackageMixin
from briefcase.integrations.xcode import verify_xcode_install


class macOSXcodeMixin(macOSMixin):
    output_format = 'Xcode'

    def verify_tools(self):
        if self.host_os != 'Darwin':
            raise BriefcaseCommandError("""
    macOS applications require the Xcode command line tools, which are
    only available on macOS.
    """)
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
            / '{app.formal_name}'.format(app=app)
            / 'build' / 'Release'
            / '{app.formal_name}.app'.format(app=app)
        )

    def distribution_path(self, app, packaging_format):
        if packaging_format == 'dmg':
            return self.platform_path / '{app.formal_name}-{app.version}.dmg'.format(
                app=app)
        else:
            return self.binary_path(app)

    def entitlements_path(self, app):
        return (
                self.bundle_path(app)
                / '{app.formal_name}'.format(app=app)
                / '{app.app_name}.entitlements'.format(app=app)
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

        print()
        print('[{app.app_name}] Building XCode project...'.format(
            app=app
        ))

        # build_settings = [
        #     ('AD_HOC_CODE_SIGNING_ALLOWED', 'YES'),
        #     ('CODE_SIGN_IDENTITY', '-'),
        #     ('VALID_ARCHS', '"i386 x86_64"'),
        #     ('ARCHS', 'x86_64'),
        #     ('ONLY_ACTIVE_ARCHS', 'NO')
        # ]
        # build_settings_str = ['{}={}'.format(*x) for x in build_settings]

        try:
            print()
            self.subprocess.run(
                [
                    'xcodebuild',  # ' '.join(build_settings_str),
                    '-project', self.bundle_path(app) / '{app.formal_name}.xcodeproj'.format(app=app),
                    '-quiet',
                    '-configuration', 'Release',
                    'build'
                ],
                check=True,
            )
            print('Build succeeded.')
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Unable to build app {app.app_name}.".format(app=app)
            )


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
