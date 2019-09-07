from briefcase.commands import (
    CreateCommand,
    UpdateCommand,
    BuildCommand,
    RunCommand,
    PublishCommand
)
from briefcase.platforms.macos import MacOSMixin


class MacOSDmgMixin(MacOSMixin):
    pass


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
