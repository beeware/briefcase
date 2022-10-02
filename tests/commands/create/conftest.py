from unittest import mock

import pytest
import tomli_w
from cookiecutter.main import cookiecutter

from briefcase.commands import CreateCommand
from briefcase.config import AppConfig
from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from tests.utils import DummyConsole


class DefaultCreateCommand(CreateCommand):
    # An instance of CreateCommand that inherits the default
    # behavior of create handling.

    # Two methods that are required by the interface, but are not needed
    # for these tests.
    def binary_path(self, app):
        return NotImplementedError()

    def distribution_path(self, app, packaging_format):
        return NotImplementedError()


@pytest.fixture
def default_create_command(tmp_path):
    return DefaultCreateCommand(base_path=tmp_path, logger=Log(), console=Console())


class DummyCreateCommand(CreateCommand):
    """A dummy create command that stubs out all the required interfaces of the
    Create command."""

    platform = "tester"
    output_format = "dummy"
    description = "Dummy create command"

    def __init__(self, *args, support_file=None, git=None, home_path=None, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(*args, **kwargs)

        # Override the host properties
        self.tools.host_arch = "gothic"
        self.tools.host_os = "c64"

        self.tools.home_path = home_path

        # If a test sets this property, the tool verification step will
        # fail.
        self._missing_tool = None

        # Mock the external services
        self.tools.git = git
        self.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
        self.support_file = support_file
        self.tools.input = DummyConsole()
        self.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)

    @property
    def support_package_url_query(self):
        """The query arguments to use in a support package query request."""
        return [
            ("platform", self.platform),
            ("version", self.python_version_tag),
            ("arch", self.tools.host_arch),
        ]

    def bundle_path(self, app):
        return self.platform_path / f"{app.app_name}.bundle"

    def binary_path(self, app):
        return self.platform_path / f"{app.app_name}.binary"

    def distribution_path(self, app, packaging_format):
        return self.platform_path / f"{app.app_name}.dummy.{packaging_format}"

    # Hard code the python version to make testing easier.
    @property
    def python_version_tag(self):
        return "3.X"

    # Define output format-specific template context.
    def output_format_template_context(self, app):
        return {"output_format": "dummy"}


class TrackingCreateCommand(DummyCreateCommand):
    """A dummy creation command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.actions = []

    def verify_tools(self):
        super().verify_tools()
        self.actions.append(("verify",))

    def verify_app_tools(self, app):
        super().verify_app_tools(app=app)
        self.actions.append(("verify-app-tools", app))

    # Override all the body methods of a CreateCommand
    # with versions that we can use to track actions performed.
    def generate_app_template(self, app):
        self.actions.append(("generate", app))

        # A mock version of template generation.
        self.bundle_path(app).mkdir(parents=True, exist_ok=True)
        with (self.bundle_path(app) / "new").open("w") as f:
            f.write("new template!")

    def install_app_support_package(self, app):
        self.actions.append(("support", app))

    def install_app_dependencies(self, app):
        self.actions.append(("dependencies", app))

    def install_app_code(self, app):
        self.actions.append(("code", app))

    def install_app_resources(self, app):
        self.actions.append(("resources", app))

    def cleanup_app_content(self, app):
        self.actions.append(("cleanup", app))


@pytest.fixture
def create_command(tmp_path, mock_git):
    return DummyCreateCommand(
        base_path=tmp_path / "project",
        data_path=tmp_path / "data",
        git=mock_git,
        home_path=tmp_path / "home",
    )


@pytest.fixture
def tracking_create_command(tmp_path, mock_git):
    return TrackingCreateCommand(
        git=mock_git,
        base_path=tmp_path,
        apps={
            "first": AppConfig(
                app_name="first",
                bundle="com.example",
                version="0.0.1",
                description="The first simple app",
                sources=["src/first"],
            ),
            "second": AppConfig(
                app_name="second",
                bundle="com.example",
                version="0.0.2",
                description="The second simple app",
                sources=["src/second"],
            ),
        },
    )


@pytest.fixture
def myapp():
    return AppConfig(
        app_name="my-app",
        formal_name="My App",
        bundle="com.example",
        version="1.2.3",
        description="This is a simple app",
        sources=["src/my_app"],
        url="https://example.com",
        author="First Last",
        author_email="first@example.com",
    )


@pytest.fixture
def bundle_path(myapp, tmp_path):
    # Return the bundle path for the app; however, as a side effect,
    # ensure that the app, app_packages and support target directories
    # exist, and the briefcase index file has been created.
    bundle_path = tmp_path / "project" / "tester" / f"{myapp.app_name}.bundle"
    (bundle_path / "path" / "to" / "app").mkdir(parents=True, exist_ok=True)
    (bundle_path / "path" / "to" / "support").mkdir(parents=True, exist_ok=True)

    return bundle_path


@pytest.fixture
def app_packages_path_index(bundle_path):
    (bundle_path / "path" / "to" / "app_packages").mkdir(parents=True, exist_ok=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "app_packages_path": "path/to/app_packages",
                "support_path": "path/to/support",
                "support_revision": 37,
            }
        }
        tomli_w.dump(index, f)


@pytest.fixture
def app_requirements_path_index(bundle_path):
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "app_requirements_path": "path/to/requirements.txt",
                "support_path": "path/to/support",
                "support_revision": 37,
            }
        }
        tomli_w.dump(index, f)


@pytest.fixture
def no_support_revision_index(bundle_path):
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "app_requirements_path": "path/to/requirements.txt",
                "support_path": "path/to/support",
            }
        }
        tomli_w.dump(index, f)


@pytest.fixture
def no_support_path_index(bundle_path):
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "app_requirements_path": "path/to/requirements.txt",
            }
        }
        tomli_w.dump(index, f)


@pytest.fixture
def support_path(bundle_path):
    return bundle_path / "path" / "to" / "support"


@pytest.fixture
def app_requirements_path(bundle_path):
    return bundle_path / "path" / "to" / "requirements.txt"


@pytest.fixture
def app_packages_path(bundle_path):
    return bundle_path / "path" / "to" / "app_packages"


@pytest.fixture
def app_path(bundle_path):
    return bundle_path / "path" / "to" / "app"
