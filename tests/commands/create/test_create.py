from briefcase.commands import CreateCommand

import pytest

from ...utils import SimpleAppConfig


class DummyCreateCommand(CreateCommand):
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
    def generate_app_template(self, app, bundle_path):
        self.actions.append(('generate', app, bundle_path))

        bundle_path.mkdir(parents=True)
        with open(bundle_path / 'new', 'w') as f:
            f.write('new template!')

    def install_app_support_package(self, app, bundle_path):
        self.actions.append(('support', app, bundle_path))

    def install_app_dependencies(self, app, bundle_path):
        self.actions.append(('dependencies', app, bundle_path))

    def install_app_code(self, app, bundle_path):
        self.actions.append(('code', app, bundle_path))

    def install_app_extras(self, app, bundle_path):
        self.actions.append(('extras', app, bundle_path))


@pytest.fixture
def create_command():
    return DummyCreateCommand(
        apps={
            'first': SimpleAppConfig(name='first'),
            'second': SimpleAppConfig(name='second'),
        }
    )


def test_create_app(create_command, tmp_path):
    "If the app doesn't already exist, it will be created"
    bundle_path = tmp_path / 'tester' / 'first.dummy'

    create_command.create_app(create_command.apps['first'], bundle_path)

    # The right sequence of things will be done
    assert create_command.actions == [
        ('generate', create_command.apps['first'], bundle_path),
        ('support', create_command.apps['first'], bundle_path),
        ('dependencies', create_command.apps['first'], bundle_path),
        ('code', create_command.apps['first'], bundle_path),
        ('extras', create_command.apps['first'], bundle_path),
    ]

    # New app content has been created
    assert (bundle_path / 'new').exists()


def test_create_existing_app_overwrite(create_command, tmp_path, monkeypatch):
    "An existing app can be overwritten if requested"
    # Answer yes when asked
    monkeypatch.setattr('builtins.input', lambda prompt: 'y')

    bundle_path = tmp_path / 'tester' / 'first.dummy'
    bundle_path.mkdir(parents=True)
    with open(bundle_path / 'original', 'w') as f:
        f.write('original template!')

    create_command.create_app(create_command.apps['first'], bundle_path)

    # The right sequence of things will be done
    assert create_command.actions == [
        ('generate', create_command.apps['first'], bundle_path),
        ('support', create_command.apps['first'], bundle_path),
        ('dependencies', create_command.apps['first'], bundle_path),
        ('code', create_command.apps['first'], bundle_path),
        ('extras', create_command.apps['first'], bundle_path),
    ]

    # Original content has been deleted
    assert not (bundle_path / 'original').exists()

    # New app content has been created
    assert (bundle_path / 'new').exists()


def test_create_existing_app_no_overwrite(create_command, tmp_path, monkeypatch):
    "If you say no, the existing app won't be overwritten"
    # Answer no when asked
    monkeypatch.setattr('builtins.input', lambda prompt: 'n')

    bundle_path = tmp_path / 'tester' / 'first.dummy'
    bundle_path.mkdir(parents=True)
    with open(bundle_path / 'original', 'w') as f:
        f.write('original template!')

    create_command.create_app(create_command.apps['first'], bundle_path)

    # No app creation actions will be performed
    assert create_command.actions == []

    # Original content still exists
    assert (bundle_path / 'original').exists()

    # New app content has not been created
    assert not (bundle_path / 'new').exists()


def test_create_existing_app_no_overwrite_default(create_command, tmp_path, monkeypatch):
    "By default, the existing app won't be overwritten"
    # Answer '' (i.e., just press return) when asked
    monkeypatch.setattr('builtins.input', lambda prompt: '')

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


# def test_create_app(create_command, tmp_path):
#     create_command.create_app(, tmp_path)


def test_create(create_command, tmp_path):
    bundle_path = tmp_path / 'tester'

    create_command(path=tmp_path)

    # The right sequence of things will be done
    assert create_command.actions == [
        ('verify'),

        # Create the first app
        ('generate', create_command.apps['first'], bundle_path / 'first.dummy'),
        ('support', create_command.apps['first'], bundle_path / 'first.dummy'),
        ('dependencies', create_command.apps['first'], bundle_path / 'first.dummy'),
        ('code', create_command.apps['first'], bundle_path / 'first.dummy'),
        ('extras', create_command.apps['first'], bundle_path / 'first.dummy'),
        # Create the second app
        ('generate', create_command.apps['second'], bundle_path / 'second.dummy'),
        ('support', create_command.apps['second'], bundle_path / 'second.dummy'),
        ('dependencies', create_command.apps['second'], bundle_path / 'second.dummy'),
        ('code', create_command.apps['second'], bundle_path / 'second.dummy'),
        ('extras', create_command.apps['second'], bundle_path / 'second.dummy'),
    ]

    # New app content has been created
    assert (bundle_path / 'first.dummy' / 'new').exists()
    assert (bundle_path / 'second.dummy' / 'new').exists()
