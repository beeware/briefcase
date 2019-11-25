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
    output_format = 'app'

    def distribution_path(self, app):
        return self.platform_path / '{app.formal_name}.dmg'.format(app=app)


class macOSDmgCreateCommand(macOSDmgMixin, macOSAppCreateCommand):
    description = "Create and populate a macOS .dmg bundle."


class macOSDmgUpdateCommand(macOSDmgMixin, macOSAppUpdateCommand):
    description = "Update an existing macOS .dmg bundle."


class macOSDmgBuildCommand(macOSDmgMixin, macOSAppBuildCommand):
    description = "Build a macOS .dmg bundle."

    def build_app(self, app: BaseConfig):
        print("MAKE A DMG")


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
