import pytest

from briefcase.commands import PublishCommand
from briefcase.commands.base import full_kwargs
from briefcase.config import AppConfig


class DummyPublishCommand(PublishCommand):
    """
    A dummy publish command that doesn't actually do anything.
    It only serves to track which actions would be performend.
    """
    platform = 'tester'
    output_format = 'dummy'
    description = 'Dummy publish command'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, apps=[], **kwargs)

        self.actions = []

    def bundle_path(self, app):
        return self.platform_path / '{app.app_name}.dummy'.format(app=app)

    def binary_path(self, app):
        return self.platform_path / '{app.app_name}.dummy.bin'.format(app=app)

    def distribution_path(self, app):
        return self.platform_path / '{app.app_name}.dummy.dist'.format(app=app)

    @property
    def publication_channels(self):
        return ['s3', 'alternative']

    @property
    def default_publication_channel(self):
        return 's3'

    def publish_app(self, app, channel, **kwargs):
        self.actions.append(('publish', app.app_name, channel, kwargs))
        return full_kwargs({
            'publish_state': app.app_name
        }, kwargs)

    # These commands override the default behavior, simply tracking that
    # they were invoked, rather than instantiating a Create/Update/Build command.
    # This is for testing purposes.
    def create_command(self, app, **kwargs):
        self.actions.append(('create', app.app_name, kwargs))
        return full_kwargs({
            'create_state': app.app_name
        }, kwargs)

    def update_command(self, app, **kwargs):
        self.actions.append(('update', app.app_name, kwargs))
        return full_kwargs({
            'update_state': app.app_name
        }, kwargs)

    def build_command(self, app, **kwargs):
        self.actions.append(('build', app.app_name, kwargs))
        return full_kwargs({
            'build_state': app.app_name
        }, kwargs)


@pytest.fixture
def publish_command(tmp_path):
    return DummyPublishCommand(base_path=tmp_path)


@pytest.fixture
def first_app_config():
    return AppConfig(
        app_name='first',
        bundle='com.example',
        version='0.0.1',
        description='The first simple app',
        sources=['src/first'],
    )


@pytest.fixture
def first_app_unbuilt(first_app_config, tmp_path):
    # The same fixture as first_app_config,
    # but ensures that the bundle for the app exists
    (tmp_path / 'tester').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'tester' / 'first.dummy').open('w') as f:
        f.write('first.bundle')

    return first_app_config


@pytest.fixture
def first_app(first_app_unbuilt, tmp_path):
    # The same fixture as first_app_config,
    # but ensures that the binary for the app exists
    with (tmp_path / 'tester' / 'first.dummy.bin').open('w') as f:
        f.write('first.exe')

    return first_app_unbuilt


@pytest.fixture
def second_app_config():
    return AppConfig(
        app_name='second',
        bundle='com.example',
        version='0.0.2',
        description='The second simple app',
        sources=['src/second'],
    )


@pytest.fixture
def second_app(second_app_config, tmp_path):
    # The same fixture as second_app_config,
    # but ensures that the binary for the app exists
    (tmp_path / 'tester').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'tester' / 'second.dummy').open('w') as f:
        f.write('second.bundle')
    with (tmp_path / 'tester' / 'second.dummy.bin').open('w') as f:
        f.write('second.exe')

    return second_app_config
