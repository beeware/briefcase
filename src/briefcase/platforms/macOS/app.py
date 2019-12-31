import itertools
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
from briefcase.console import select_option
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import get_identities
from briefcase.platforms.macOS import macOSMixin


class macOSAppMixin(macOSMixin):
    output_format = 'app'

    def binary_path(self, app):
        return self.bundle_path(app) / '{app.formal_name}.app'.format(app=app)

    def distribution_path(self, app):
        return self.binary_path(app)


class macOSAppCreateCommand(macOSAppMixin, CreateCommand):
    description = "Create and populate a macOS app."


class macOSAppUpdateCommand(macOSAppMixin, UpdateCommand):
    description = "Update an existing macOS app."


class macOSAppBuildCommand(macOSAppMixin, BuildCommand):
    description = "Build a macOS app."


class macOSAppRunCommand(macOSAppMixin, RunCommand):
    description = "Run a macOS app."

    def run_app(self, app: BaseConfig, **kwargs):
        """
        Start the application.

        :param app: The config object for the app
        :param base_path: The path to the project directory.
        """
        print()
        print('[{app.app_name}] Starting app...'.format(
            app=app
        ))
        try:
            print()
            self.subprocess.run(
                [
                    'open',
                    self.binary_path(app),
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Unable to start app {app.app_name}.".format(app=app)
            )


class macOSAppPackageCommand(macOSAppMixin, PackageCommand):
    description = "Package a macOS app for distribution."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External service APIs.
        # These are abstracted to enable testing without patching.
        self.get_identities = get_identities

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            '--no-sign',
            dest='sign_app',
            help='Disable code signing of .app bundles.',
            action='store_false',
        )
        parser.add_argument(
            '-i',
            '--identity',
            dest='identity',
            help='The code signing identity to use; either the 40-digit hex '
                 'checksum, or the full name of the identity.',
            required=False,
        )

    def select_identity(self, identity=None):
        """
        Get the codesigning identity to use.

        :param identity: A pre-specified identity (either the 40-digit
            hex checksum, or the string name of the identity). If provided, it
            will be validated against the list of available identities to
            confirm that it is a valid codesigning identity.
        :returns: The final identity to use
        """
        # Obtain the valid codesigning identities.
        identities = self.get_identities('codesigning')

        if identity:
            try:
                # Try to look up the identity as a hex checksum
                return identities[identity]
            except KeyError:
                # It's not a valid checksum; try to use it as a value.
                if identity in identities.values():
                    return identity

            raise BriefcaseCommandError(
                "Invalid code signing identity {identity!r}".format(
                    identity=identity
                )
            )

        if len(identities) == 0:
            raise BriefcaseCommandError(
                "No code signing identities are available."
            )
        elif len(identities) == 1:
            identity = list(identities.items())[0][1]
        else:
            print()
            print("Select code signing identity to use:")
            print()
            selection = select_option(identities, input=self.input)
            identity = identities[selection]
            print("selected", identity)

        return identity

    def sign(self, path, entitlements, identity):
        """
        Code sign a file.

        :param path: The path to the file to sign.
        :param entitlements: The path to the entitlements file to use.
        :param identity: The code signing identity to use. Either the 40-digit
            hex checksum, or the string name of the identity.
        """
        try:
            print("Signing", path)
            self.subprocess.run(
                [
                    'codesign',
                    '--sign', identity,
                    '--entitlements', str(entitlements),
                    '--deep', str(path),
                    '--force',
                    '--options', 'runtime',
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Unable to code sign {path}.".format(path=path)
            )

    def package_app(self, app: BaseConfig, sign_app=True, identity=None, **kwargs):
        """
        Prepare the .app bundle for distribution.

        This involves code signing.

        :param app: The application to package
        :param sign_app: Should the application be signed?
        :param identity: The code signing identity to use. This can be either
            the 40-digit hex checksum, or the string name of the identity.
            If unspecified, the user will be prompted for a code signing
            identity. Ignored if ``sign_app`` is False.
        """
        if sign_app:
            identity = self.select_identity(identity=identity)

            print()
            print("[{app.app_name}] Signing app with identity {identity}...".format(
                app=app,
                identity=identity
            ))

            for path in itertools.chain(
                self.binary_path(app).glob('**/*.so'),
                self.binary_path(app).glob('**/*.dylib'),
                [self.binary_path(app)],
            ):
                self.sign(
                    path,
                    entitlements=self.bundle_path(app) / 'Entitlements.plist',
                    identity=identity,
                )


class macOSAppPublishCommand(macOSAppMixin, PublishCommand):
    description = "Publish a macOS app."


# Declare the briefcase command bindings
create = macOSAppCreateCommand  # noqa
update = macOSAppUpdateCommand  # noqa
build = macOSAppBuildCommand  # noqa
run = macOSAppRunCommand  # noqa
package = macOSAppPackageCommand  # noqa
publish = macOSAppPublishCommand  # noqa
