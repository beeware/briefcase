from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.platforms.macos import MacOSMixin


class MacOSAppMixin(MacOSMixin):
    def __init__(self):
        super().__init__(output_format='app')

    def binary_path(self, app, base_path):
        return base_path / 'macOS' / '{app.formal_name}.app'.format(app=app)

    def bundle_path(self, app, base_path):
        return base_path / 'macOS' / '{app.formal_name}.app'.format(app=app)

    @property
    def support_package_url(self):
        return 'https://pybee-briefcase-support.s3-us-west-2.amazonaws.com/Python-Apple-support/3.7/macOS/Python-3.7-macOS-support.b1.tar.gz'

    def support_path(self, app, bundle_path):
        return bundle_path


class MacOSAppCreateCommand(MacOSAppMixin, CreateCommand):
    description = "Create and populate a macOS .app bundle."
    template_url = 'https://github.com/beeware/Python-macOS-template.git'


class MacOSAppUpdateCommand(MacOSAppMixin, UpdateCommand):
    description = "Update an existing macOS .app bundle."


class MacOSAppBuildCommand(MacOSAppMixin, BuildCommand):
    description = "Build a macOS .app bundle."


class MacOSAppRunCommand(MacOSAppMixin, RunCommand):
    description = "Run a macOS .app bundle."


class MacOSAppPublishCommand(MacOSAppMixin, PublishCommand):
    description = "Publish a macOS .app bundle."

    def add_options(self, parser):
        parser.add_argument(
            '-c',
            '--channel',
            choices=['s3', 'github', 'appstore'],
            default='s3',
            metavar='channel',
            help='The channel to publish to'
        )


# Declare the briefcase command bindings
create = MacOSAppCreateCommand  # noqa
update = MacOSAppUpdateCommand  # noqa
build = MacOSAppBuildCommand  # noqa
run = MacOSAppRunCommand  # noqa
publish = MacOSAppPublishCommand  # noqa
