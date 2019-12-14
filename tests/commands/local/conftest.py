import pytest

from briefcase.commands import LocalCommand
from briefcase.commands.base import full_kwargs
from briefcase.config import AppConfig


class DummyLocalCommand(LocalCommand):
    """
    A dummy Local command that doesn't actually do anything.
    It only serves to track which actions would be performend.
    """
    platform = 'tester'
    output_format = 'dummy'
    description = 'Dummy local command'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, apps=[], **kwargs)

        self.actions = []

    def install_local_app_dependencies(self, app, **kwargs):
        self.actions.append(('local_app_dependencies', app.name, kwargs))

    def run_local_app(self, app, **kwargs):
        self.actions.append(('run_local', app.name, kwargs))
        return full_kwargs({
            'run_local_state': app.name
        }, kwargs)


@pytest.fixture
def local_command(tmp_path):
    return DummyLocalCommand(base_path=tmp_path)


@pytest.fixture
def first_app(tmp_path):
    # Make sure the source code exists
    (tmp_path / 'src' / 'first').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'src' / 'first' / '__init__.py').open('w') as f:
        f.write('print("Hello world")')

    return AppConfig(
        name='first',
        bundle='com.example',
        version='0.0.1',
        description='The first simple app',
        sources=['src/first'],
    )


@pytest.fixture
def second_app(tmp_path):
    # Make sure the source code exists
    (tmp_path / 'src' / 'second').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'src' / 'second' / '__init__.py').open('w') as f:
        f.write('print("Hello world")')

    return AppConfig(
        name='second',
        bundle='com.example',
        version='0.0.2',
        description='The second simple app',
        sources=['src/second'],
    )
