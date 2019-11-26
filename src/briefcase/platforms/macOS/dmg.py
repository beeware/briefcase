import dmgbuild

from briefcase.config import BaseConfig
from briefcase.platforms.macOS.app import (
    macOSAppMixin,
    macOSAppCreateCommand,
    macOSAppUpdateCommand,
    macOSAppBuildCommand,
    macOSAppRunCommand,
    macOSAppPublishCommand
)


class macOSDmgMixin(macOSAppMixin):
    output_format = 'dmg'

    def distribution_path(self, app):
        return self.platform_path / '{app.formal_name}-{app.version}.dmg'.format(app=app)


class macOSDmgCreateCommand(macOSDmgMixin, macOSAppCreateCommand):
    description = "Create and populate a macOS .dmg bundle."


class macOSDmgUpdateCommand(macOSDmgMixin, macOSAppUpdateCommand):
    description = "Update an existing macOS .dmg bundle."


class macOSDmgBuildCommand(macOSDmgMixin, macOSAppBuildCommand):
    description = "Build a macOS .dmg bundle."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External service APIs.
        # These are abstracted to enable testing without patching.
        self.dmgbuild = dmgbuild

    def build_app(self, app: BaseConfig, **kwargs):
        print()
        print("[{app.name}] Building DMG...".format(app=app))

        dmg_settings = {
            'files': [str(self.bundle_path(app))],
            'symlinks': {'Applications': '/Applications'},
            'icon_locations': {
                '{app.formal_name}.app'.format(app=app): (100, 100),
                'Applications': (300, 100),
            },
        }

        try:
            icon = app.installer_icon
            if isinstance(icon, str) and icon.endswith('.icns'):
                dmg_settings['icon'] = self.base_path / icon
        except AttributeError:
            # No installer icon provided.
            # If a single .icns file has been provided as an app icon,
            # use that instead.
            try:
                icon = app.icon
                if isinstance(icon, str) and icon.endswith('.icns'):
                    dmg_settings['icon'] = self.base_path / icon
            except AttributeError:

                pass

        try:
            dmg_settings['background'] = self.base_path / app.installer_background
        except AttributeError:
            # No installer background image provided
            pass

        self.dmgbuild.build_dmg(
            filename=self.distribution_path(app),
            volume_name='{app.formal_name} {app.version}'.format(app=app),
            settings=dmg_settings
        )


class macOSDmgRunCommand(macOSDmgMixin, macOSAppRunCommand):
    description = "Run a macOS .dmg bundle."


class macOSDmgPublishCommand(macOSDmgMixin, macOSAppPublishCommand):
    description = "Publish a macOS .dmg bundle."

    def add_options(self):
        self.parser.add_argument(
            '-c',
            '--channel',
            choices=['s3', 'github', 'appstore'],
            default='s3',
            metavar='channel',
            help='The channel to publish to'
        )


# Declare the briefcase command bindings
create = macOSDmgCreateCommand  # noqa
update = macOSDmgUpdateCommand  # noqa
build = macOSDmgBuildCommand  # noqa
run = macOSDmgRunCommand  # noqa
publish = macOSDmgPublishCommand  # noqa
