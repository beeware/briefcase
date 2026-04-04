from unittest.mock import MagicMock

import briefcase.commands.new
from briefcase.bootstraps import TogaGuiBootstrap


def test_create_bootstrap(new_command, mock_builtin_bootstraps, monkeypatch):
    """A bootstrap can be selected and instantiated."""
    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(return_value=mock_builtin_bootstraps),
    )

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    selected, bootstraps = new_command.select_bootstrap(
        project_overrides={"bootstrap": "Toga"},
    )
    bootstrap = bootstraps[selected](console=new_command.console, context=context)

    assert isinstance(bootstrap, TogaGuiBootstrap)
    assert bootstrap.context == context
