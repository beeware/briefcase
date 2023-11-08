import logging

import pytest

from briefcase.console import LogLevel, RichLoggingHandler
from briefcase.exceptions import UnsupportedHostError
from briefcase.integrations.git import Git


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.git = "tool"

    tool = Git.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.git


def test_unsupported_os(mock_tools):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = "wonky"

    with pytest.raises(
        UnsupportedHostError,
        match=f"{Git.name} is not supported on wonky",
    ):
        Git.verify(mock_tools)


@pytest.mark.parametrize(
    "logging_level, handler_expected",
    [
        (LogLevel.DEEP_DEBUG, True),
        (LogLevel.DEBUG, False),
        (LogLevel.VERBOSE, False),
        (LogLevel.INFO, False),
    ],
)
def test_git_stdlib_logging(mock_tools, logging_level, handler_expected):
    """A logging handler is configured for GitPython when DEEP_DEBUG is enabled."""
    mock_tools.logger.verbosity = logging_level

    Git.verify(mock_tools)

    assert handler_expected is any(
        isinstance(h, RichLoggingHandler) for h in logging.getLogger("git").handlers
    )

    # reset handlers since they are persistent
    logging.getLogger("git").handlers.clear()
