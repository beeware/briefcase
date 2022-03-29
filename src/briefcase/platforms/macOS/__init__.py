import itertools
import os
import subprocess
import stat

from briefcase.config import BaseConfig
from briefcase.console import select_option
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import (
    get_identities,
    verify_command_line_tools_install
)

try:
    import dmgbuild
except ImportError:
    # On non-macOS platforms, dmgbuild won't be installed.
    # Allow the plugin to be loaded; raise an error when tools are verified.
    dmgbuild = None


DEFAULT_OUTPUT_FORMAT = 'app'


class macOSMixin:
    platform = 'macOS'


class macOSRunMixin:
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
            self.subprocess.run(
                [
                    'open',
                    '-n',  # Force a new app to be launched
                    os.fsdecode(self.binary_path(app)),
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Unable to start app {app.app_name}.".format(app=app)
            )

        # Start streaming logs for the app.
        try:
            print()
            print("[{app.app_name}] Following system log output (type CTRL-C to stop log)...".format(app=app))
            print("=" * 75)
            # Streaming the system log is... a mess. The system log contains a
            # *lot* of noise from other processes; even if you filter by
            # process, there's a lot of macOS-generated noise. It's very
            # difficult to extract just the "user generated" stdout/err log
            # messages.
            #
            # The following sets up a log stream filter that looks for:
            #  1. a log sender that matches that app binary; or,
            #  2. a log sender of libffi, and a process that matches the app binary.
            # Case (1) works for pre-Python 3.9 static linked binaries.
            # Case (2) works for Python 3.9+ dynamic linked binaries.
            self.subprocess.run(
                [
                    "log",
                    "stream",
                    "--style", "compact",
                    "--predicate",
                    'senderImagePath=="{sender}"'
                    ' OR (processImagePath=="{sender}"'
                    ' AND senderImagePath=="/usr/lib/libffi.dylib")'.format(
                        sender=os.fsdecode(self.binary_path(app) / "Contents" / "MacOS" / app.formal_name)
                    )
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Unable to start log stream for app {app.app_name}.".format(app=app)
            )


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
            # Try to look up the identity as a hex checksum
            if identity in identities:
                return identity

            # Try to look up the identity as readable name
            identity_by_name = next(((hex_key,name) for hex_key,name in identities.items()
                                    if identity in name), None)
            if identity_by_name is not None:
                if identity_by_name[1] == identity:
                    return identity_by_name[1]
                else:
                    raise BriefcaseCommandError(
                        "Invalid code signing identity {identity!r}. (Did you mean {found!r}?)".format(
                            identity=identity, found=identity_by_name[1],
                        )
                    )

            # Not found
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
            print(f"selected '{identity}")

        return identity

    def sign(self, path, identity, entitlements=None):
        """
        Code sign a file.

        :param path: The path to the file to sign.
        :param identity: The code signing identity to use. Either the 40-digit
            hex checksum, or the string name of the identity.
        :param entitlements: The path to the entitlements file to use.
        """
        options = 'runtime' if identity != '-' else None
        process_command = [
            'codesign',
            '--sign', identity,
            str(path),
            '--force',
        ]
        if entitlements:
            process_command.append('--entitlements')
            process_command.append(str(entitlements))
        if options:
            process_command.append('--options')
            process_command.append(options)

        while True:
            try:
                print("Signing:", ' '.join((f"'{pc}'" if ' ' in pc else pc for pc in process_command)))
                self.subprocess.run(
                    process_command,
                    stderr=subprocess.PIPE,
                    check=True,
                )
                break
            except subprocess.CalledProcessError as e:
                errors = e.stderr.decode('utf-8', errors='replace')
                print(errors)
                if 'not signed at all' in errors and '--deep' not in process_command:
                    # The lexicographic order was not enough to resolve the dependencies
                    # Retry with --deep
                    process_command.append('--deep')
                    continue
                if 'unsupported format for signature' in errors:
                    # We should not be signing this in the first place
                    print("Skipping signature for:", path)
                    if path.suffix == '.cstemp':
                        print("     (this looks like a temporary file from codesign -- "
                                "if that's the case it can be safely removed)"
                        )
                    return
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

            def validate_mach_o(filename):
                with open(filename, 'rb') as f:
                    magic = f.read(4)
                return magic in (b'\xCA\xFE\xBA\xBE', b'\xCF\xFA\xED\xFE', b'\xCE\xFA\xED\xFE',
                                 b'\xBE\xBA\xFE\xCA', b'\xFE\xED\xFA\xCF', b'\xFE\xED\xFA\xCE',)

            # Signs code objects in reversed lexicographic order to ensure nesting order is respected
            # (objects must be signed from the inside out)
            bundle_path = self.binary_path(app)
            resources_path = bundle_path / 'Contents'/ 'Resources'
            all_files = ((f,os.stat(f).st_mode,) for f in resources_path.rglob('*'))
            exec_suffixes = ('.dylib', '.o', '.so', '')
            exec_files = (f for f,m in all_files if (not stat.S_ISDIR(m)) and
                                ((m & stat.S_IXUSR) or f.suffix.lower() in exec_suffixes))
            exec_binaries = (f for f in exec_files if validate_mach_o(f))

            final_bundle = (bundle_path,)
            bundles = itertools.chain(
                            resources_path.rglob('*.framework'),
                            resources_path.rglob('*.app'),
                            final_bundle,
                        )
            sign_targets = sorted(itertools.chain(exec_binaries, bundles), reverse=True)
            for path in sign_targets:
                self.sign(
                    path,
                    entitlements=self.entitlements_path(app),
                    identity=identity,
                )

        if packaging_format == 'dmg':

            print()
            print('[{app.app_name}] Building DMG...'.format(app=app))

            dmg_settings = {
                'files': [os.fsdecode(self.binary_path(app))],
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
                dmg_settings['icon'] = os.fsdecode(icon_filename)

            try:
                image_filename = self.base_path / '{image}.png'.format(
                    image=app.installer_background
                )
                if image_filename.exists():
                    dmg_settings['background'] = os.fsdecode(image_filename)
                else:
                    print("Can't find {filename}.png for DMG background".format(
                        filename=app.installer_background
                    ))
            except AttributeError:
                # No installer background image provided
                pass

            dmg_path = os.fsdecode(self.distribution_path(app, packaging_format=packaging_format))
            self.dmgbuild.build_dmg(
                filename=dmg_path,
                volume_name='{app.formal_name} {app.version}'.format(app=app),
                settings=dmg_settings
            )

            if sign_app:
                self.sign(
                    dmg_path,
                    identity=identity,
                )
