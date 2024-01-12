from __future__ import annotations

from unittest import mock

import pytest
import tomli_w
from cookiecutter.main import cookiecutter

from briefcase.commands import CreateCommand
from briefcase.config import AppConfig
from briefcase.console import Console, Log
from briefcase.integrations.base import Tool
from briefcase.integrations.subprocess import Subprocess

from ...utils import DummyConsole, create_file


@pytest.fixture
def monkeypatch_tool_host_os(monkeypatch):
    """Add testing host OS as supported for tools that support all platforms."""
    monkeypatch.setattr(
        Tool,
        "supported_host_os",
        Tool.supported_host_os.union({"c64"}),
    )


class DefaultCreateCommand(CreateCommand):
    # An instance of CreateCommand that inherits the default
    # behavior of create handling.

    # method is required by the interface, but are not needed for these tests.
    def binary_path(self, app):
        return NotImplementedError()


@pytest.fixture
def default_create_command(tmp_path):
    return DefaultCreateCommand(base_path=tmp_path, logger=Log(), console=Console())


class DummyCreateCommand(CreateCommand):
    """A dummy create command that stubs out all the required interfaces of the Create
    command."""

    supported_host_os = {"c64"}
    # Platform and format contain upper case to test case normalization
    platform = "Tester"
    output_format = "Dummy"
    description = "Dummy create command"
    hidden_app_properties = {"permission", "request"}

    def __init__(self, *args, support_file=None, git=None, home_path=None, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(*args, **kwargs)

        # Override the host properties
        self.tools.host_arch = "gothic"
        self.tools.host_os = "c64"

        self.tools.home_path = home_path

        # If a test sets this property, the tool verification step will fail.
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

    def binary_path(self, app):
        return self.bundle_path(app) / f"{app.app_name}.bin"

    # Hard code the python version to make testing easier.
    @property
    def python_version_tag(self):
        return "3.X"

    # Define output format-specific template context.
    def output_format_template_context(self, app):
        return {"output_format": "dummy"}

    # Handle platform-specific permissions.
    # Convert all the cross-platform permissions to upper case, prefixing DUMMY_.
    # Add a "good lighting" request if the camera permission has been requested.
    def permissions_context(self, app: AppConfig, x_permissions: dict[str, str]):
        # We don't actually need anything from the superclass; but call it to ensure
        # coverage.
        context = super().permissions_context(app, x_permissions)
        if context:
            # Make sure the base class *isn't* doing anything.
            return context

        permissions = {
            f"DUMMY_{key.upper()}": value.upper()
            for key, value in x_permissions.items()
            if value
        }
        context["permissions"] = permissions
        context["custom_permissions"] = app.permission

        requests = {"good.lighting": True} if x_permissions["camera"] else {}
        requests.update(getattr(app, "request", {}))
        context["requests"] = requests

        return context


class TrackingCreateCommand(DummyCreateCommand):
    """A dummy creation command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.actions = []

    def briefcase_toml(self, app):
        # default any app to an empty `briefcase.toml`
        return self._briefcase_toml.get(app, {})

    def verify_host(self):
        super().verify_host()
        self.actions.append(("verify-host",))

    def verify_tools(self):
        super().verify_tools()
        self.actions.append(("verify-tools",))

    def finalize_app_config(self, app):
        super().finalize_app_config(app=app)
        self.actions.append(("finalize-app-config", app.app_name))

    def verify_app_template(self, app):
        super().verify_app_template(app=app)
        self.actions.append(("verify-app-template", app.app_name))

    def verify_app_tools(self, app):
        super().verify_app_tools(app=app)
        self.actions.append(("verify-app-tools", app.app_name))

    # Override all the body methods of a CreateCommand
    # with versions that we can use to track actions performed.
    def generate_app_template(self, app):
        self.actions.append(("generate", app.app_name))

        # A mock version of template generation.
        create_file(self.bundle_path(app) / "new", "new template!")

    def install_app_support_package(self, app):
        self.actions.append(("support", app.app_name))

    def install_app_requirements(self, app, test_mode):
        self.actions.append(("requirements", app.app_name, test_mode))

    def install_app_code(self, app, test_mode):
        self.actions.append(("code", app.app_name, test_mode))

    def install_app_resources(self, app):
        self.actions.append(("resources", app.app_name))

    def cleanup_app_content(self, app):
        self.actions.append(("cleanup", app.app_name))


@pytest.fixture
def create_command(tmp_path, mock_git, monkeypatch_tool_host_os):
    return DummyCreateCommand(
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "data",
        git=mock_git,
        home_path=tmp_path / "home",
    )


@pytest.fixture
def tracking_create_command(tmp_path, mock_git, monkeypatch_tool_host_os):
    return TrackingCreateCommand(
        git=mock_git,
        base_path=tmp_path / "base_path",
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
    # ensure that the app, and app_packages target directories
    # exist, and the briefcase index file has been created.
    bundle_path = tmp_path / "base_path/build" / myapp.app_name / "tester/dummy"
    (bundle_path / "path/to/app").mkdir(parents=True, exist_ok=True)

    return bundle_path


@pytest.fixture
def app_packages_path_index(bundle_path):
    (bundle_path / "path/to/app_packages").mkdir(parents=True, exist_ok=True)
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
    return bundle_path / "path/to/support"


@pytest.fixture
def app_requirements_path(bundle_path):
    return bundle_path / "path/to/requirements.txt"


@pytest.fixture
def app_packages_path(bundle_path):
    return bundle_path / "path/to/app_packages"


@pytest.fixture
def app_path(bundle_path):
    return bundle_path / "path/to/app"
