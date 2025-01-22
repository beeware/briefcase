import os
from unittest import mock

import pytest

from briefcase.console import Console


@pytest.fixture
def console(monkeypatch) -> Console:
    console = Console()
    console._console_impl.input = mock.MagicMock(spec_set=input)
    # default console is always interactive
    monkeypatch.setattr(os, "isatty", lambda _: True)
    return console


@pytest.fixture
def disabled_console() -> Console:
    console = Console(input_enabled=False)
    console._console_impl.input = mock.MagicMock(spec_set=input)
    return console


@pytest.fixture
def non_interactive_console(console, monkeypatch) -> Console:
    monkeypatch.setattr(os, "isatty", lambda _: False)
    yield console
