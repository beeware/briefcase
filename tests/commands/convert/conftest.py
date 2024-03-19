from tempfile import TemporaryDirectory

import pytest

import briefcase.commands.convert
from briefcase.commands import ConvertCommand
from briefcase.commands.base import full_options
from briefcase.console import Console, Log
from tests.utils import DummyConsole


class DummyConvertCommand(ConvertCommand):
    """A dummy convert command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    description = "Dummy convert command"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(*args, apps={}, **kwargs)

        self.actions = []
        self.tools.input = DummyConsole()

    def verify_host(self):
        super().verify_host()
        self.actions.append(("verify-host",))

    def verify_tools(self):
        super().verify_tools()
        self.actions.append(("verify-tools",))

    def finalize_app_config(self, app):
        super().finalize_app_config(app=app)
        self.actions.append(("finalize-app-config", app))

    def verify_app_tools(self, app):
        super().verify_app_tools(app=app)
        self.actions.append(("verify-app-tools", app.app_name))

    def validate_pyproject_file(self):
        super().validate_pyproject_file()
        self.actions.append(("validate-pyproject-file",))

    def validate_not_empty_project(self):
        super().validate_not_empty_project()
        self.actions.append(("validate-not-empty-project",))

    def convert_app(self, **kwargs):
        self.actions.append(("new", kwargs))
        return full_options({"new_state": "done"}, kwargs)


@pytest.fixture
def tmp_path_generator(tmp_path):
    """Generator that creates and returns a new temporary directory when next is called
    on it."""

    def gen():
        i = 0
        while True:
            out = tmp_path / str(hash(str(i)))
            out.mkdir()
            yield out
            i += 1

    return gen()


@pytest.fixture
def convert_command(tmp_path_generator):
    return DummyConvertCommand(base_path=next(tmp_path_generator))


@pytest.fixture
def patch_tempdir(monkeypatch):
    tmpdir = TemporaryDirectory()
    monkeypatch.setattr(
        briefcase.commands.convert, "TemporaryDirectory", lambda: tmpdir
    )
    return tmpdir
