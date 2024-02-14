import sys
from unittest import mock

import pytest

from briefcase.console import Console


@pytest.fixture
def console(monkeypatch) -> Console:
    console = Console()
    console.input = mock.MagicMock(spec_set=input)
    # default console is always interactive
    monkeypatch.setattr(sys.__stdout__, "isatty", lambda: True)
    return console


@pytest.fixture
def disabled_console() -> Console:
    console = Console(enabled=False)
    console.input = mock.MagicMock(spec_set=input)
    return console


@pytest.fixture
def non_interactive_console(console, monkeypatch) -> Console:
    monkeypatch.setattr(sys.__stdout__, "isatty", lambda: False)
    yield console
