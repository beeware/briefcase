import inspect
from unittest import mock

import pytest
from git import exc as git_exceptions

from briefcase.console import Printer

# Stop Rich from inserting line breaks in to long lines of text.
# Rich does this to prevent individual words being split between
# two lines in the terminal...however, these additional line breaks
# cause some tests to fail unexpectedly.
Printer.console.soft_wrap = True


@pytest.fixture
def mock_git():
    git = mock.MagicMock()
    git.exc = git_exceptions

    return git


def monkeypatched_print(*arg, **kwargs):
    """Raise an error for calls to print."""
    frame = inspect.currentframe().f_back
    module = inspect.getmodule(frame.f_code)

    # Disallow any use of a bare print() in the briefcase codebase
    if (
        module.__name__.startswith("briefcase.")
        and module.__name__ != "briefcase.console"
    ):
        pytest.fail(
            "print() should not be invoked directly. Use Log or Console for printing."
        )


@pytest.fixture(autouse=True)
def no_print(monkeypatch):
    """Replace builtin print function for ALL tests."""
    monkeypatch.setattr("builtins.print", monkeypatched_print)
