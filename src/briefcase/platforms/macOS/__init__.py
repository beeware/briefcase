import subprocess
import itertools

from briefcase.config import BaseConfig
from briefcase.console import select_option
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import get_identities
from briefcase.integrations.xcode import verify_command_line_tools_install

try:
    import dmgbuild
except ImportError:
    # On non-macOS platforms, dmgbuild won't be installed.
    # Allow the plugin to be loaded; raise an error when tools are verified.
    dmgbuild = None


DEFAULT_OUTPUT_FORMAT = 'app'


class macOSMixin:
    platform = 'macOS'


class macOSPackageMixin:

    @property
    def packaging_formats(self):
        return ['app', 'dmg']

    @property
    def default_packaging_format(self):
        return 'dmg'

    def verify_tools(self):

        if self.host_os != 'Darwin':
            raise BriefcaseCommandError("""
        Code signing and / or building a DMG requires running on macOS.
        """)

        # Require the XCode command line tools.
        verify_command_line_tools_install(self)

        # Verify superclass tools *after* xcode. This ensures we get the
        # git check *after* the xcode check.
        super().verify_tools()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External service APIs.
        # These are abstracted to enable testing without patching.
        self.get_identities = get_identities
        self.dmgbuild = dmgbuild

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
        identities = self.get_identities(self, 'codesigning')

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

    def package_app(
            self,
            app: BaseConfig,
            sign_app=True,
            identity=None,
            adhoc_sign=False,
            packaging_format='dmg',
            **kwargs
    ):
        """
        Package an app bundle.

        :param app: The application to package
        :param sign_app: Should the application be signed?
        :param identity: The code signing identity to use. This can be either
            the 40-digit hex checksum, or the string name of the identity.
            If unspecified, the user will be prompted for a code signing
            identity. Ignored if ``sign_app`` is False.
        :param adhoc_sign: If true, code will be signed with adhoc identity of "-"
        :param packaging_format: The packaging format to use. Default is `dmg`.
        """

        if sign_app:
            if adhoc_sign:
                identity = "-"

                print()
                print("[{app.app_name}] Signing app with adhoc identity...".format(app=app))
            else:
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
                    entitlements=self.entitlements_path(app),
                    identity=identity,
                )

        if packaging_format == 'dmg':

            print()
            print('[{app.app_name}] Building DMG...'.format(app=app))

            dmg_settings = {
                'files': [str(self.binary_path(app))],
                'symlinks': {'Applications': '/Applications'},
                'icon_locations': {
                    '{app.formal_name}.app'.format(app=app): (75, 75),
                    'Applications': (225, 75),
                },
                'window_rect': ((600, 600), (350, 150)),
                'icon_size': 64,
                'text_size': 12,
            }

            try:
                icon_filename = self.base_path / '{icon}.icns'.format(
                    icon=app.installer_icon
                )
                if not icon_filename.exists():
                    print("Can't find {filename}.icns for DMG installer icon".format(
                        filename=app.installer_icon
                    ))
                    raise AttributeError()
            except AttributeError:
                # No installer icon specified. Fall back to the app icon
                try:
                    icon_filename = self.base_path / '{icon}.icns'.format(
                        icon=app.icon
                    )
                    if not icon_filename.exists():
                        print("Can't find {filename}.icns for fallback DMG installer icon".format(
                            filename=app.icon
                        ))
                        raise AttributeError()
                except AttributeError:
                    icon_filename = None

            if icon_filename:
                dmg_settings['icon'] = str(icon_filename)

            try:
                image_filename = self.base_path / '{image}.png'.format(
                    image=app.installer_background
                )
                if image_filename.exists():
                    dmg_settings['background'] = str(image_filename)
                else:
                    print("Can't find {filename}.png for DMG background".format(
                        filename=app.installer_background
                    ))
            except AttributeError:
                # No installer background image provided
                pass

            self.dmgbuild.build_dmg(
                filename=str(self.distribution_path(app, packaging_format=packaging_format)),
                volume_name='{app.formal_name} {app.version}'.format(app=app),
                settings=dmg_settings
            )
