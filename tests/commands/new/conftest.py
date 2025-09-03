from unittest.mock import MagicMock

import pytest

from briefcase.commands import NewCommand
from briefcase.commands.base import full_options


class DummyNewCommand(NewCommand):
    """A dummy new command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    description = "Dummy new command"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, apps={}, **kwargs)

        self.actions = []

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
def new_command(dummy_console, tmp_path):
    command = DummyNewCommand(
        console=dummy_console,
        base_path=tmp_path,
    )
    command.get_git_config_value = MagicMock(return_value=None)
    return command
