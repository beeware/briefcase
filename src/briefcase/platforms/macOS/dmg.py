from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.platforms.macOS import macOSMixin


class macOSDmgMixin(macOSMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, output_format='dmg', **kwargs)

    def binary_path(self, app):
        return self.platform_path / '{app.formal_name}.app'.format(app=app)

    def bundle_path(self, app):
        return self.platform_path / '{app.formal_name}.app'.format(app=app)


class macOSDmgCreateCommand(macOSDmgMixin, CreateCommand):
    description = "Create and populate a macOS .dmg bundle."


class macOSDmgUpdateCommand(macOSDmgMixin, UpdateCommand):
    description = "Update an existing macOS .dmg bundle."


class macOSDmgBuildCommand(macOSDmgMixin, BuildCommand):
    description = "Build a macOS .dmg bundle."


class macOSDmgRunCommand(macOSDmgMixin, RunCommand):
    description = "Run a macOS .dmg bundle."


class macOSDmgPublishCommand(macOSDmgMixin, PublishCommand):
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
