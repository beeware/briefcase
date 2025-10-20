import os

import pytest

from briefcase.console import Console

from ...utils import DummyConsole


@pytest.fixture
def raw_console() -> Console:
    console = Console()
    yield console
    console.close()


@pytest.fixture
def console(monkeypatch) -> DummyConsole:
    console = DummyConsole()
    # default console is always interactive
    monkeypatch.setattr(os, "isatty", lambda _: True)
    yield console
    console.close()


@pytest.fixture
def disabled_console() -> DummyConsole:
    console = DummyConsole(input_enabled=False)
    yield console
    console.close()


@pytest.fixture
def non_interactive_console(console, monkeypatch) -> DummyConsole:
    monkeypatch.setattr(os, "isatty", lambda _: False)
    return console
