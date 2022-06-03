from unittest import mock

import pytest

from briefcase.console import Console


@pytest.fixture
def console():
    console = Console()
    console.rich_console.input = mock.MagicMock()
    return console


@pytest.fixture
def disabled_console():
    console = Console(enabled=False)
    console.rich_console.input = mock.MagicMock()
    return console
