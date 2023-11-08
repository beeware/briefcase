import logging

import pytest

from briefcase.console import LogLevel, RichLoggingHandler

cookiecutter_logger = logging.getLogger("cookiecutter")


@pytest.fixture
def base_command(base_command):
    # Mock actual templating commands as no-ops
    base_command.update_cookiecutter_cache = lambda *a, **kw: None
    base_command.tools.cookiecutter = lambda *a, **kw: None
    return base_command


@pytest.mark.parametrize(
    "logging_level, handler_expected",
    [
        (LogLevel.DEEP_DEBUG, True),
        (LogLevel.DEBUG, False),
        (LogLevel.VERBOSE, False),
        (LogLevel.INFO, False),
    ],
)
def test_git_stdlib_logging(base_command, logging_level, handler_expected):
    """A logging handler is configured for GitPython when DEEP_DEBUG is enabled."""
    base_command.logger.verbosity = logging_level

    base_command.generate_template(
        template="", branch="", output_path="", extra_context={}
    )

    assert handler_expected is any(
        isinstance(h, RichLoggingHandler)
        for h in logging.getLogger("cookiecutter").handlers
    )

    # reset handlers since they are persistent
    logging.getLogger("cookiecutter").handlers.clear()
