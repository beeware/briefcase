import pytest

from briefcase.commands import UpdateCommand
from briefcase.config import AppConfig
from briefcase.console import Console, Log

from ...utils import create_file


class DummyUpdateCommand(UpdateCommand):
    """A dummy update command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    # Platform and format contain upper case to test case normalization
    platform = "Tester"
    output_format = "Dummy"
    description = "Dummy update command"

    def __init__(self, *args, apps, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(*args, apps=apps, **kwargs)

        self.actions = []

    def briefcase_toml(self, app):
        # default any app to an empty `briefcase.toml`
        return self._briefcase_toml.get(app, {})

    def binary_path(self, app):
        return self.bundle_path(app) / f"{app.app_name}.bin"

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

    # Override all the body methods of a UpdateCommand
    # with versions that we can use to track actions performed.
    def install_app_requirements(self, app, test_mode):
        self.actions.append(("requirements", app.app_name, test_mode))
        create_file(self.bundle_path(app) / "requirements", "app requirements")

    def install_app_code(self, app, test_mode):
        self.actions.append(("code", app.app_name, test_mode))
        create_file(self.bundle_path(app) / "code.py", "print('app')")

    def install_app_resources(self, app):
        self.actions.append(("resources", app.app_name))
        create_file(self.bundle_path(app) / "resources", "app resources")

    def cleanup_app_support_package(self, app):
        self.actions.append(("cleanup-support", app.app_name))

    def install_app_support_package(self, app):
        self.actions.append(("support", app.app_name))
        create_file(self.bundle_path(app) / "support/content.txt", "app support")

    def cleanup_app_content(self, app):
        self.actions.append(("cleanup", app.app_name))


@pytest.fixture
def update_command(tmp_path):
    return DummyUpdateCommand(
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
def first_app(tmp_path):
    """Populate skeleton app content for the first app."""
    create_file(
        tmp_path
        / "base_path"
        / "build"
        / "first"
        / "tester"
        / "dummy"
        / "first.bundle",
        "first.bundle",
    )


@pytest.fixture
def second_app(tmp_path):
    """Populate skeleton app content for the second app."""
    create_file(
        tmp_path
        / "base_path"
        / "build"
        / "second"
        / "tester"
        / "dummy"
        / "second.bundle",
        "second.bundle",
    )
