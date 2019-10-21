import pytest

from briefcase.config import AppConfig
from briefcase.commands import UpdateCommand


class DummyUpdateCommand(UpdateCommand):
    """
    A dummy creation command that doesn't actually do anything.
    It only serves to track which actions would be performend.
    """
    def __init__(self, apps):
        super().__init__(platform='tester', output_format='dummy', apps=apps)

        self.actions = []

    def bundle_path(self, app, base):
        return base / 'tester' / '{app.name}.dummy'.format(app=app)

    def binary_path(self, app, base):
        return base / 'tester' / '{app.name}.dummy.bin'.format(app=app)

    def verify_tools(self):
        self.actions.append(('verify'))

    # Override all the body methods of a UpdateCommand
    # with versions that we can use to track actions performed.
    def install_app_dependencies(self, app, base_path):
        self.actions.append(('dependencies', app, base_path))
        with open(self.bundle_path(app, base_path) / 'dependencies', 'w') as f:
            f.write("first app dependencies")

    def install_app_code(self, app, base_path):
        self.actions.append(('code', app, base_path))
        with open(self.bundle_path(app, base_path) / 'code.py', 'w') as f:
            f.write("print('first app')")


@pytest.fixture
def update_command():
    return DummyUpdateCommand(
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


@pytest.fixture
def first_app(tmp_path):
    "Populate skeleton app content for the first app"
    bundle_dir = tmp_path / "tester" / "first.dummy"
    bundle_dir.mkdir(parents=True)
    with open(bundle_dir / 'Content', 'w') as f:
        f.write("first app.exe")


@pytest.fixture
def second_app(tmp_path):
    "Populate skeleton app content for the second app"
    bundle_dir = tmp_path / "tester" / "second.dummy"
    bundle_dir.mkdir(parents=True)
    with open(bundle_dir / 'Content', 'w') as f:
        f.write("second app.exe")
