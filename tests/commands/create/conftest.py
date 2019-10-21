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
    def __init__(self, *args, support_file=None, **kwargs):
        super().__init__(*args, platform='tester', output_format='dummy', **kwargs)

        # If a test sets this property, the tool verification step will
        # fail.
        self._missing_tool = None

        # Mock the external services
        self.git = mock.MagicMock()
        self.cookiecutter = mock.MagicMock()
        self.subprocess = mock.MagicMock()
        self.support_file = support_file

    def bundle_path(self, app):
        return self.platform_path / '{app.name}.bundle'.format(app=app)

    def binary_path(self, app):
        return self.platform_path / '{app.name}.binary'.format(app=app)

    # Hard code the python version to make testing easier.
    @property
    def python_version_tag(self):
        return '3.X'


@pytest.fixture
def create_command(tmp_path):
    return DummyCreateCommand(base_path=tmp_path)


@pytest.fixture
def myapp():
    return AppConfig(
        name='my-app',
        formal_name='My App',
        bundle='com.example',
        version='1.2.3',
        description='This is a simple app',
    )


@pytest.fixture
def bundle_path(myapp, tmp_path):
    # Return the bundle path for the app; however, as a side effect,
    # ensure that the app, app_packages and support target directories
    # exist, and the briefcase index file has been created.
    bundle_path = tmp_path / 'tester' / '{myapp.name}.bundle'.format(myapp=myapp)
    (bundle_path / 'path' / 'to' / 'app').mkdir(parents=True, exist_ok=True)
    (bundle_path / 'path' / 'to' / 'app_packages').mkdir(parents=True, exist_ok=True)
    (bundle_path / 'path' / 'to' / 'support').mkdir(parents=True, exist_ok=True)
    with open(bundle_path / 'briefcase.toml', 'w') as f:
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
