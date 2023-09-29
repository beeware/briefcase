import logging

import pytest

cookiecutter_logger = logging.getLogger("cookiecutter")


@pytest.fixture
def base_command(base_command):
    # Mock actual templating commands as no-ops
    base_command.update_cookiecutter_cache = lambda *a, **kw: None
    base_command.tools.cookiecutter = lambda *a, **kw: None
    return base_command


@pytest.mark.parametrize(
    "verbosity, log_level",
    [
        (0, logging.INFO),
        (1, logging.INFO),
        (2, logging.DEBUG),
    ],
)
def test_cookiecutter_logging_config(base_command, verbosity, log_level):
    """The loggers for cookiecutter are configured as expected."""
    base_command.logger.verbosity = verbosity

    base_command.generate_template(
        template="", branch="", output_path="", extra_context={}
    )
    # call multiple times to ensure only 1 handler ever exists
    base_command.generate_template(
        template="", branch="", output_path="", extra_context={}
    )

    assert len(cookiecutter_logger.handlers) == 1
    assert cookiecutter_logger.handlers[0].level == log_level
