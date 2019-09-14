from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)


class DummyMixin:
    def binary_path(self):
        raise NotImplementedError()

    def bundle_path(self):
        raise NotImplementedError()


class DummyCreateCommand(DummyMixin, CreateCommand):
    description = "Create and populate a dummy bundle."


class DummyUpdateCommand(DummyMixin, UpdateCommand):
    description = "Update an existing dummy bundle."


class DummyBuildCommand(DummyMixin, BuildCommand):
    description = "Build a dummy bundle."


class DummyRunCommand(DummyMixin, RunCommand):
    description = "Run a dummy bundle."


class DummyPublishCommand(DummyMixin, PublishCommand):
    description = "Publish a dummy bundle."


# Declare the briefcase command bindings
create = DummyCreateCommand  # noqa
update = DummyUpdateCommand  # noqa
build = DummyBuildCommand  # noqa
run = DummyRunCommand  # noqa
publish = DummyPublishCommand  # noqa
