import inspect
from unittest import mock

import pytest
from git import exc as git_exceptions


@pytest.fixture
def mock_git():
    git = mock.MagicMock()
    git.exc = git_exceptions

    return git


# preserve print so sanctioned callers can still use it
_print = print


def monkeypatched_print(*arg, **kwargs):
    "Allow print calls from console.py...raise an error for all other callers"
    frame = inspect.currentframe().f_back
    module = inspect.getmodule(frame.f_code)

    # Disallow any use of a bare print() in the briefcase codebase
    if module.__name__.startswith("briefcase.") and module.__name__ != "briefcase.console":
        pytest.fail(
            "print() should not be invoked directly. Use Log or Console for printing."
        )
    else:
        _print(*arg, **kwargs)


@pytest.fixture(autouse=True)
def no_print(monkeypatch):
    "Replace builtin print function for ALL tests"
    monkeypatch.setattr("builtins.print", monkeypatched_print)
