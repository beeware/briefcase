from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.platforms.linux import LinuxMixin


class AppImageMixin(LinuxMixin):
    def __init__(self):
        super().__init__(output_format='appimage')

    def binary_path(self, app, base_path):
        raise NotImplementedError()

    def bundle_path(self, app, base_path):
        raise NotImplementedError()

    @property
    def support_package_url(self):
        raise NotImplementedError()

    def support_path(self, app, bundle_path):
        raise NotImplementedError()


class LinuxAppImageCreateCommand(AppImageMixin, CreateCommand):
    description = "Create and populate a Linux AppImage."
    template_url = 'https://github.com/beeware/Python-linux-template.git'


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
