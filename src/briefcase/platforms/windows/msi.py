from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.platforms.windows import WindowsMixin


class MSIMixin(WindowsMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, output_format='msi', **kwargs)

    def binary_path(self, app):
        raise NotImplementedError()

    def bundle_path(self, app):
        raise NotImplementedError()


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


# Declare the briefcase command bindings
create = WindowsMSICreateCommand  # noqa
update = WindowsMSIUpdateCommand  # noqa
build = WindowsMSIBuildCommand  # noqa
run = WindowsMSIRunCommand  # noqa
publish = WindowsMSIPublishCommand  # noqa
