import sys
from contextlib import suppress
from pathlib import Path

from briefcase.cmdline import parse_cmdline
from briefcase.console import Console, Log, Printer
from briefcase.exceptions import (
    BriefcaseError,
    BriefcaseTestSuiteFailure,
    BriefcaseWarning,
    HelpText,
)


def main():
    result = 0
    command = None
    printer = Printer()
    console = Console(printer=printer)
    logger = Log(printer=printer)
    try:
        Command, extra_cmdline = parse_cmdline(sys.argv[1:], console=console)
        command = Command(logger=logger, console=console)
        options, overrides = command.parse_options(extra=extra_cmdline)
        command.parse_config(
            Path.cwd() / "pyproject.toml",
            overrides=overrides,
        )
        command(**options)
    except HelpText as e:
        logger.info()
        logger.info(str(e))
        result = e.error_code
    except BriefcaseWarning as w:
        # The case of something that hasn't gone right, but in an
        # acceptable way.
        logger.warning(str(w))
        result = w.error_code
    except BriefcaseTestSuiteFailure as e:
        # Test suite status is logged when the test is executed.
        # Set the return code, but don't log anything else.
        result = e.error_code
    except BriefcaseError as e:
        logger.error()
        logger.error(str(e))
        result = e.error_code
        logger.capture_stacktrace()
    except Exception:
        logger.capture_stacktrace()
        raise
    except KeyboardInterrupt:
        logger.warning()
        logger.warning("Aborted by user.")
        logger.warning()
        result = -42
        if logger.save_log:
            logger.capture_stacktrace()
    finally:
        with suppress(KeyboardInterrupt):
            logger.save_log_to_file(command)

    return result


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
