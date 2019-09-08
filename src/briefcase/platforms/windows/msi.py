from briefcase.commands import (
    CreateCommand,
    UpdateCommand,
    BuildCommand,
    RunCommand,
    PublishCommand
)
from briefcase.platforms.windows import WindowsMixin


class MSIMixin(WindowsMixin):
    pass


class WindowsMSICreateCommand(MSIMixin, CreateCommand):
    description = "Create and populate a Windows MSI."


class WindowsMSIUpdateCommand(MSIMixin, UpdateCommand):
    description = "Update an existing Windows MSI."


class WindowsMSIBuildCommand(MSIMixin, BuildCommand):
    description = "Build a Windows MSI."


class WindowsMSIRunCommand(MSIMixin, RunCommand):
    description = "Run a Windows MSI."


class WindowsMSIPublishCommand(MSIMixin, PublishCommand):
    description = "Publish a Windows MSI."

    def add_options(self):
        self.parser.add_argument(
            '-c',
            '--channel',
            choices=['s3', 'github', 'appstore'],
            default='s3',
            help='The channel to publish to'
        )


# Declare the briefcase command bindings
create = WindowsMSICreateCommand  # noqa
update = WindowsMSIUpdateCommand  # noqa
build = WindowsMSIBuildCommand  # noqa
run = WindowsMSIRunCommand  # noqa
publish = WindowsMSIPublishCommand  # noqa
