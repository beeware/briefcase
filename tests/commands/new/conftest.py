import pytest

from briefcase.commands import NewCommand
from briefcase.commands.base import full_options
from briefcase.console import Console, Log
from tests.utils import DummyConsole


class DummyNewCommand(NewCommand):
    """A dummy new command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    description = "Dummy new command"

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

    def new_app(self, **kwargs):
        self.actions.append(("new", kwargs))
        return full_options({"new_state": "done"}, kwargs)


@pytest.fixture
def new_command(tmp_path):
    return DummyNewCommand(base_path=tmp_path)
