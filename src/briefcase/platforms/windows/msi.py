from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.platforms.windows import WindowsMixin


class MSIMixin(WindowsMixin):
    def __init__(self):
        super().__init__(output_format='msi')

    def binary_path(self, app, base_path):
        raise NotImplementedError()

    def bundle_path(self, app, base_path):
        raise NotImplementedError()


class WindowsMSICreateCommand(MSIMixin, CreateCommand):
    description = "Create and populate a Windows MSI."
    template_url = 'https://github.com/beeware/Python-windows-template.git'


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
