import pytest

from briefcase.commands import DevCommand
from briefcase.commands.base import full_kwargs
from briefcase.config import AppConfig


class DummyDevCommand(DevCommand):
    """
    A dummy Dev command that doesn't actually do anything.
    It only serves to track which actions would be performend.
    """
    platform = 'tester'
    output_format = 'dummy'
    description = 'Dummy dev command'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, apps=[], **kwargs)

        self.actions = []

    def install_dev_dependencies(self, app, **kwargs):
        self.actions.append(('dev_dependencies', app.app_name, kwargs))

    def run_dev_app(self, app, **kwargs):
        self.actions.append(('run_dev', app.app_name, kwargs))
        return full_kwargs({
            'run_dev_state': app.app_name
        }, kwargs)


@pytest.fixture
def dev_command(tmp_path):
    return DummyDevCommand(base_path=tmp_path)


@pytest.fixture
def first_app_uninstalled(tmp_path):
    # Make sure the source code exists
    (tmp_path / 'src' / 'first').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'src' / 'first' / '__init__.py').open('w') as f:
        f.write('print("Hello world")')

    return AppConfig(
        app_name='first',
        bundle='com.example',
        version='0.0.1',
        description='The first simple app',
        sources=['src/first'],
    )


@pytest.fixture
def first_app(tmp_path, first_app_uninstalled):
    # The same fixture as first_app_uninstalled,
    # but ensures that the .dist-info folder for the app exists
    (tmp_path / 'src' / 'first.dist-info').mkdir(exist_ok=True)
    return first_app_uninstalled


@pytest.fixture
def second_app(tmp_path):
    # Make sure the source code exists
    (tmp_path / 'src' / 'second').mkdir(parents=True, exist_ok=True)
    with (tmp_path / 'src' / 'second' / '__init__.py').open('w') as f:
        f.write('print("Hello world")')

    # Create the dist-info folder
    (tmp_path / 'src' / 'second.dist-info').mkdir(exist_ok=True)

    return AppConfig(
        app_name='second',
        bundle='com.example',
        version='0.0.2',
        description='The second simple app',
        sources=['src/second'],
    )
