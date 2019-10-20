from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.platforms.macos import MacOSMixin


class MacOSDmgMixin(MacOSMixin):
    def __init__(self):
        super().__init__(output_format='dmg')

    def binary_path(self, app, base_path):
        return base_path / 'macOS' / '{app.formal_name}.dmg'

    def bundle_path(self, app, base_path):
        return base_path / 'macOS' / '{app.formal_name}.app'


class MacOSDmgCreateCommand(MacOSDmgMixin, CreateCommand):
    description = "Create and populate a macOS .dmg bundle."


class MacOSDmgUpdateCommand(MacOSDmgMixin, UpdateCommand):
    description = "Update an existing macOS .dmg bundle."


class MacOSDmgBuildCommand(MacOSDmgMixin, BuildCommand):
    description = "Build a macOS .dmg bundle."


class MacOSDmgRunCommand(MacOSDmgMixin, RunCommand):
    description = "Run a macOS .dmg bundle."


class MacOSDmgPublishCommand(MacOSDmgMixin, PublishCommand):
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
create = MacOSDmgCreateCommand  # noqa
update = MacOSDmgUpdateCommand  # noqa
build = MacOSDmgBuildCommand  # noqa
run = MacOSDmgRunCommand  # noqa
publish = MacOSDmgPublishCommand  # noqa
