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


def mock_print(*arg, **kwargs):
    "Allow print calls from console.py...raise an error for all other callers"
    frame = inspect.currentframe().f_back
    module = inspect.getmodule(frame.f_code)
    if module.__name__ == "briefcase.console":
        _print(*arg, **kwargs)
    else:
        pytest.fail(
            "Do not directly call the print function. "
            "Instead, use either Log or Console for printing."
        )


@pytest.fixture(autouse=True)
def no_print(monkeypatch):
    "Replace builtin print function for ALL tests"
    monkeypatch.setattr("builtins.print", mock_print)
