from unittest import mock

import pytest

from briefcase.config import AppConfig
from briefcase.commands import CreateCommand


class DummyCreateCommand(CreateCommand):
    """
    A dummy creation command that doesn't actually do anything.
    It only serves to track which actions would be performend.
    """
    def __init__(self, apps):
        super().__init__(platform='tester', output_format='dummy', apps=apps)

        self.actions = []

    @property
    def template_url(self):
        return 'https://github.com/beeware/briefcase-sample-template.git'

    def bundle_path(self, app, base):
        return base / 'tester' / '{app.name}.dummy'.format(app=app)

    def binary_path(self, app, base):
        return base / 'tester' / '{app.name}.dummy.bin'.format(app=app)

    def verify_tools(self):
        self.actions.append(('verify'))

    # Override all the body methods of a CreateCommand
    # with versions that we can use to track actions performed.
    def generate_app_template(self, app, base_path):
        self.actions.append(('generate', app, base_path))

        # A mock version of template generation.
        bundle_path = base_path / 'tester' / '{app.name}.dummy'.format(app=app)
        bundle_path.mkdir(parents=True, exist_ok=True)
        with open(bundle_path / 'new', 'w') as f:
            f.write('new template!')

    def install_app_support_package(self, app, base_path):
        self.actions.append(('support', app, base_path))

    def install_app_dependencies(self, app, base_path):
        self.actions.append(('dependencies', app, base_path))

    def install_app_code(self, app, base_path):
        self.actions.append(('code', app, base_path))

    def install_app_extras(self, app, base_path):
        self.actions.append(('extras', app, base_path))


@pytest.fixture
def create_command():
    return DummyCreateCommand(
        apps={
            'first': AppConfig(
                name='first',
                bundle='com.example',
                version='0.0.1',
                description='The first simple app',
            ),
            'second': AppConfig(
                name='second',
                bundle='com.example',
                version='0.0.2',
                description='The second simple app',
            ),
        }
    )


def test_create_app(create_command, tmp_path):
    "If the app doesn't already exist, it will be created"
    create_command.create_app(create_command.apps['first'], tmp_path)

    # The right sequence of things will be done
    assert create_command.actions == [
        ('generate', create_command.apps['first'], tmp_path),
        ('support', create_command.apps['first'], tmp_path),
        ('dependencies', create_command.apps['first'], tmp_path),
        ('code', create_command.apps['first'], tmp_path),
        ('extras', create_command.apps['first'], tmp_path),
    ]

    # New app content has been created
    assert (tmp_path / 'tester' / 'first.dummy' / 'new').exists()


def test_create_existing_app_overwrite(create_command, tmp_path):
    "An existing app can be overwritten if requested"
    # Answer yes when asked
    create_command.input = mock.MagicMock(return_value='y')

    # Generate an app in the location.
    bundle_path = tmp_path / 'tester' / 'first.dummy'
    bundle_path.mkdir(parents=True)
    with open(bundle_path / 'original', 'w') as f:
        f.write('original template!')

    create_command.create_app(create_command.apps['first'], tmp_path)

    # The right sequence of things will be done
    assert create_command.actions == [
        ('generate', create_command.apps['first'], tmp_path),
        ('support', create_command.apps['first'], tmp_path),
        ('dependencies', create_command.apps['first'], tmp_path),
        ('code', create_command.apps['first'], tmp_path),
        ('extras', create_command.apps['first'], tmp_path),
    ]

    # Original content has been deleted
    assert not (bundle_path / 'original').exists()

    # New app content has been created
    assert (bundle_path / 'new').exists()


def test_create_existing_app_no_overwrite(create_command, tmp_path):
    "If you say no, the existing app won't be overwritten"
    # Answer no when asked
    create_command.input = mock.MagicMock(return_value='n')

    bundle_path = tmp_path / 'tester' / 'first.dummy'
    bundle_path.mkdir(parents=True)
    with open(bundle_path / 'original', 'w') as f:
        f.write('original template!')

    create_command.create_app(create_command.apps['first'], tmp_path)

    # No app creation actions will be performed
    assert create_command.actions == []

    # Original content still exists
    assert (bundle_path / 'original').exists()

    # New app content has not been created
    assert not (bundle_path / 'new').exists()


def test_create_existing_app_no_overwrite_default(create_command, tmp_path):
    "By default, the existing app won't be overwritten"
    # Answer '' (i.e., just press return) when asked
    create_command.input = mock.MagicMock(return_value='')

    bundle_path = tmp_path / 'tester' / 'first.dummy'
    bundle_path.mkdir(parents=True)
    with open(bundle_path / 'original', 'w') as f:
        f.write('original template!')

    create_command.create_app(create_command.apps['first'], tmp_path)

    assert create_command.actions == []

    # Original content still exists
    assert (bundle_path / 'original').exists()

    # New app content has not been created
    assert not (bundle_path / 'new').exists()
