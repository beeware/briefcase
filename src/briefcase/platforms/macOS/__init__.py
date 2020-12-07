import itertools

from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import verify_command_line_tools_install

try:
    import dmgbuild
except ImportError:
    # On non-macOS platforms, dmgbuild won't be installed.
    # Allow the plugin to be loaded; raise an error when tools are verified.
    dmgbuild = None


DEFAULT_OUTPUT_FORMAT = 'dmg'


class macOSMixin:
    platform = 'macOS'

    def verify_tools(self):
        if self.host_os != 'Darwin':
            raise BriefcaseCommandError("""
macOS applications require the Xcode command line tools, which are
only available on macOS.
""")
        # Require the XCode command line tools.
        verify_command_line_tools_install(self)

        # Verify superclass tools *after* xcode. This ensures we get the
        # git check *after* the xcode check.
        super().verify_tools()


class macOSPackageDMGMixin:

    def distribution_path(self, app):
        return self.platform_path / '{app.formal_name}-{app.version}.dmg'.format(app=app)

    def verify_tools(self):
        super().verify_tools()
        if dmgbuild is None:
            raise BriefcaseCommandError("A macOS DMG can only be created on macOS.")

    def package_app(
            self,
            app: BaseConfig,
            format='dmg',
            sign_app=True,
            identity=None,
            adhoc_sign=False,
            **kwargs
    ):
        """
        Build a DMG.

        :param app: The application to package
        :param sign_app: Should the application be signed?
        :param identity: The code signing identity to use. This can be either
            the 40-digit hex checksum, or the string name of the identity.
            If unspecified, the user will be prompted for a code signing
            identity. Ignored if ``sign_app`` is False.
        :param adhoc_sign: If true, code will be signed with adhoc identity of "-"
        :param format: If "dmg", package app as DMG.
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

        if format == 'dmg':

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
                filename=str(self.distribution_path(app)),
                volume_name='{app.formal_name} {app.version}'.format(app=app),
                settings=dmg_settings
            )
