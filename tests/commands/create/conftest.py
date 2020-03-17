from unittest import mock

import pytest
import toml

from briefcase.commands import CreateCommand
from briefcase.config import AppConfig


class DummyCreateCommand(CreateCommand):
    """
    A dummy create command that stubs out all the required interfaces
    of the Create command.
    """
    platform = 'tester'
    output_format = 'dummy'
    description = 'Dummy create command'

    def __init__(self, *args, support_file=None, **kwargs):
        super().__init__(*args, **kwargs)

        # If a test sets this property, the tool verification step will
        # fail.
        self._missing_tool = None

        # Mock the external services
        self.git = mock.MagicMock()
        self.cookiecutter = mock.MagicMock()
        self.subprocess = mock.MagicMock()
        self.support_file = support_file

    def bundle_path(self, app):
        return self.platform_path / '{app.app_name}.bundle'.format(app=app)

    def binary_path(self, app):
        return self.platform_path / '{app.app_name}.binary'.format(app=app)

    def distribution_path(self, app):
        return self.platform_path / '{app.app_name}.dist'.format(app=app)

    # Hard code the python version to make testing easier.
    @property
    def python_version_tag(self):
        return '3.X'

    # Define output format-specific template context.
    def output_format_template_context(self, app):
        return {
            'output_format': 'dummy'
        }


class TrackingCreateCommand(DummyCreateCommand):
    """
    A dummy creation command that doesn't actually do anything.
    It only serves to track which actions would be performend.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.actions = []

    def verify_tools(self):
        super().verify_tools()
        self.actions.append(('verify'))

    # Override all the body methods of a CreateCommand
    # with versions that we can use to track actions performed.
    def generate_app_template(self, app):
        self.actions.append(('generate', app))

        # A mock version of template generation.
        self.bundle_path(app).mkdir(parents=True, exist_ok=True)
        with (self.bundle_path(app) / 'new').open('w') as f:
            f.write('new template!')

    def install_app_support_package(self, app):
        self.actions.append(('support', app))

    def install_app_dependencies(self, app):
        self.actions.append(('dependencies', app))

    def install_app_code(self, app):
        self.actions.append(('code', app))

    def install_app_resources(self, app):
        self.actions.append(('resources', app))


@pytest.fixture
def create_command(tmp_path):
    return DummyCreateCommand(
        base_path=tmp_path,
        dot_briefcase_path=tmp_path / "dot-briefcase",
    )


@pytest.fixture
def tracking_create_command(tmp_path):
    return TrackingCreateCommand(
        base_path=tmp_path,
        apps={
            'first': AppConfig(
                app_name='first',
                bundle='com.example',
                version='0.0.1',
                description='The first simple app',
                sources=['src/first'],
            ),
            'second': AppConfig(
                app_name='second',
                bundle='com.example',
                version='0.0.2',
                description='The second simple app',
                sources=['src/second'],
            ),
        }
    )


@pytest.fixture
def myapp():
    return AppConfig(
        app_name='my-app',
        formal_name='My App',
        bundle='com.example',
        version='1.2.3',
        description='This is a simple app',
        sources=['src/my_app'],
    )


@pytest.fixture
def bundle_path(myapp, tmp_path):
    # Return the bundle path for the app; however, as a side effect,
    # ensure that the app, app_packages and support target directories
    # exist, and the briefcase index file has been created.
    bundle_path = tmp_path / 'tester' / '{myapp.app_name}.bundle'.format(myapp=myapp)
    (bundle_path / 'path' / 'to' / 'app').mkdir(parents=True, exist_ok=True)
    (bundle_path / 'path' / 'to' / 'app_packages').mkdir(parents=True, exist_ok=True)
    (bundle_path / 'path' / 'to' / 'support').mkdir(parents=True, exist_ok=True)
    with (bundle_path / 'briefcase.toml').open('w') as f:
        index = {
            'paths': {
                'app_path': 'path/to/app',
                'app_packages_path': 'path/to/app_packages',
                'support_path': 'path/to/support',
            }
        }
        toml.dump(index, f)

    return bundle_path


@pytest.fixture
def support_path(bundle_path):
    return bundle_path / 'path' / 'to' / 'support'


@pytest.fixture
def app_packages_path(bundle_path):
    return bundle_path / 'path' / 'to' / 'app_packages'


@pytest.fixture
def app_path(bundle_path):
    return bundle_path / 'path' / 'to' / 'app'
