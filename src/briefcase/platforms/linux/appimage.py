from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.platforms.linux import LinuxMixin


class AppImageMixin(LinuxMixin):
    pass


class LinuxAppImageCreateCommand(AppImageMixin, CreateCommand):
    description = "Create and populate a Linux AppImage."


class LinuxAppImageUpdateCommand(AppImageMixin, UpdateCommand):
    description = "Update an existing Linux AppImage."


class LinuxAppImageBuildCommand(AppImageMixin, BuildCommand):
    description = "Build a Linux AppImage."


class LinuxAppImageRunCommand(AppImageMixin, RunCommand):
    description = "Run a Linux AppImage."


class LinuxAppImagePublishCommand(AppImageMixin, PublishCommand):
    description = "Publish a Linux AppImage."

    def add_options(self):
        self.parser.add_argument(
            '-c',
            '--channel',
            choices=['s3', 'github', 'appstore'],
            default='s3',
            help='The channel to publish to'
        )


# Declare the briefcase command bindings
create = LinuxAppImageCreateCommand  # noqa
update = LinuxAppImageUpdateCommand  # noqa
build = LinuxAppImageBuildCommand  # noqa
run = LinuxAppImageRunCommand  # noqa
publish = LinuxAppImagePublishCommand  # noqa
