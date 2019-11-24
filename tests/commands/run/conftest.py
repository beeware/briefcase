import pytest

from briefcase.commands import RunCommand
from briefcase.config import AppConfig


class DummyRunCommand(RunCommand):
    """
    A dummy creation command that doesn't actually do anything.
    It only serves to track which actions would be performend.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, platform='tester', output_format='dummy', apps=[], **kwargs)

        self.actions = []

    def bundle_path(self, app):
        return self.platform_path / app.name

    def binary_path(self, app):
        return self.platform_path / app.name / '{app.name}.bin'.format(app=app)

    def run_app(self, app):
        self.actions.append(('run', app.name))

    # These commands override the default behavior, simply tracking that
    # they were invoked, rather than instantiating a Create/Update/Build command.
    # This is for testing purposes.
    def create_command(self, app):
        self.actions.append(('create', app.name))

    def update_command(self, app):
        self.actions.append(('update', app.name))

    def build_command(self, app):
        self.actions.append(('build', app.name))


@pytest.fixture
def run_command(tmp_path):
    return DummyRunCommand(base_path=tmp_path)


@pytest.fixture
def first_app_config():
    return AppConfig(
        name='first',
        bundle='com.example',
        version='0.0.1',
        description='The first simple app',
    )


@pytest.fixture
def first_app_uncompiled(first_app_config, tmp_path):
    # The same fixture as first_app_config,
    # but ensures that the bundle for the app exists
    (tmp_path / 'tester' / 'first').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'tester' / 'first' / 'first.dummy').open('w') as f:
        f.write('first.dummy')

    return first_app_config


@pytest.fixture
def first_app(first_app_uncompiled, tmp_path):
    # The same fixture as first_app_uncompiled,
    # but ensures that the binary for the app exists
    with (tmp_path / 'tester' / 'first' / 'first.bin').open('w') as f:
        f.write('first.bin')

    return first_app_uncompiled


@pytest.fixture
def second_app_config():
    return AppConfig(
        name='second',
        bundle='com.example',
        version='0.0.2',
        description='The second simple app',
    )


@pytest.fixture
def second_app_uncompiled(second_app_config, tmp_path):
    # The same fixture as second_app_config,
    # but ensures that the bundle for the app exists
    (tmp_path / 'tester' / 'second').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'tester' / 'second' / 'second.dummy').open('w') as f:
        f.write('second.dummy')

    return second_app_config


@pytest.fixture
def second_app(second_app_uncompiled, tmp_path):
    # The same fixture as second_app_uncompiled,
    # but ensures that the binary for the app exists
    (tmp_path / 'tester').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'tester' / 'second' / 'second.bin').open('w') as f:
        f.write('second.bin')

    return second_app_uncompiled
