import pytest

from briefcase.commands import PackageCommand
from briefcase.commands.base import full_options
from briefcase.config import AppConfig


class DummyPackageCommand(PackageCommand):
    """
    A dummy package command that doesn't actually do anything.
    It only serves to track which actions would be performend.
    """
    platform = 'tester'
    output_format = 'dummy'
    description = 'Dummy package command'

    @property
    def packaging_formats(self):
        return ['pkg', 'box']

    @property
    def default_packaging_format(self):
        return 'pkg'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, apps=[], **kwargs)

        self.actions = []

    def bundle_path(self, app):
        return self.platform_path / app.app_name

    def binary_path(self, app):
        return self.platform_path / app.app_name / '{app.app_name}.bin'.format(app=app)

    def distribution_path(self, app, packaging_format):
        return self.platform_path / '{app.app_name}.{packaging_format}'.format(
            app=app,
            packaging_format=packaging_format,
        )

    def verify_tools(self):
        super().verify_tools()
        self.actions.append(('verify',))

    def package_app(self, app, **kwargs):
        self.actions.append(('package', app.app_name, kwargs))
        return full_options({
            'package_state': app.app_name
        }, kwargs)

    # These commands override the default behavior, simply tracking that
    # they were invoked, rather than instantiating a Create/Update/Build command.
    # This is for testing purposes.
    def create_command(self, app, **kwargs):
        self.actions.append(('create', app.app_name, kwargs))
        return full_options({
            'create_state': app.app_name
        }, kwargs)

    def update_command(self, app, **kwargs):
        self.actions.append(('update', app.app_name, kwargs))
        return full_options({
            'update_state': app.app_name
        }, kwargs)

    def build_command(self, app, **kwargs):
        self.actions.append(('build', app.app_name, kwargs))
        return full_options({
            'build_state': app.app_name
        }, kwargs)


@pytest.fixture
def package_command(tmp_path):
    return DummyPackageCommand(base_path=tmp_path)


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
    (tmp_path / 'tester' / 'first').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'tester' / 'first' / 'first.dummy').open('w') as f:
        f.write('first.dummy')

    return first_app_config


@pytest.fixture
def first_app(first_app_unbuilt, tmp_path):
    # The same fixture as first_app_uncompiled,
    # but ensures that the binary for the app exists
    with (tmp_path / 'tester' / 'first' / 'first.bin').open('w') as f:
        f.write('first.bin')

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
