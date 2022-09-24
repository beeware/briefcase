import os
from unittest.mock import MagicMock

import pytest

from briefcase.commands import OpenCommand
from briefcase.commands.base import full_options
from briefcase.config import AppConfig
from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess

from ...utils import create_file


class DummyOpenCommand(OpenCommand):
    """A dummy open command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    platform = "tester"
    output_format = "dummy"
    description = "Dummy Open command"

    def __init__(self, *args, apps, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(*args, apps=apps, **kwargs)

        # Override the OS services that are used when opening
        self.tools.os = MagicMock(spec_set=os)
        self.tools.subprocess = MagicMock(spec_set=Subprocess)

        self.actions = []

    def binary_path(self, app):
        raise NotImplementedError(
            "Required by interface contract, but should not be used"
        )

    def project_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.project"

    def distribution_path(self, app, packaging_format):
        raise NotImplementedError(
            "Required by interface contract, but should not be used"
        )

    def verify_tools(self):
        super().verify_tools()
        self.actions.append(("verify",))

    def verify_app_tools(self, app):
        super().verify_app_tools(app=app)
        self.actions.append(("verify-app-tools", app.app_name))

    def open_project(self, project_path):
        super().open_project(project_path)
        self.actions.append(("open", project_path))

    # These commands override the default behavior, simply tracking that
    # they were invoked, rather than instantiating a Create command.
    # This is for testing purposes.
    def create_command(self, app, **kwargs):
        self.actions.append(("create", app.app_name, kwargs))
        return full_options({"create_state": app.app_name}, kwargs)


@pytest.fixture
def open_command(tmp_path):
    return DummyOpenCommand(
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
def first_app(tmp_path):
    """Populate skeleton app content for the first app."""
    project_file = tmp_path / "tester" / "dummy" / "first" / "first.project"
    create_file(project_file, "first project")
    return project_file


@pytest.fixture
def second_app(tmp_path):
    """Populate skeleton app content for the second app."""
    project_file = tmp_path / "tester" / "dummy" / "second" / "second.project"
    create_file(project_file, "second project")
    return project_file
