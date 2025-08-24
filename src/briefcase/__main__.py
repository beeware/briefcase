import sys
from contextlib import suppress
from pathlib import Path

from briefcase.cmdline import parse_cmdline
from briefcase.console import Console
from briefcase.exceptions import (
    BriefcaseError,
    BriefcaseTestSuiteFailure,
    BriefcaseWarning,
    HelpText,
)


def main():
    result = 0
    command = None
    console = Console()
    try:
        Command, extra_cmdline = parse_cmdline(sys.argv[1:], console=console)
        command = Command(console=console)
        options, overrides = command.parse_options(extra=extra_cmdline)
        command.parse_config(
            Path.cwd() / "pyproject.toml",
            overrides=overrides,
        )
        command(**options)
    except HelpText as e:
        console.info()
        console.info(str(e))
        result = e.error_code
    except BriefcaseWarning as w:
        # The case of something that hasn't gone right, but in an
        # acceptable way.
        console.warning(str(w))
        result = w.error_code
    except BriefcaseTestSuiteFailure as e:
        # Test suite status is logged when the test is executed.
        # Set the return code, but don't log anything else.
        result = e.error_code
    except BriefcaseError as e:
        console.error()
        console.error(str(e))
        result = e.error_code
        console.capture_stacktrace()
    except Exception:
        console.capture_stacktrace()
        raise
    except KeyboardInterrupt:
        console.warning()
        console.warning("Aborted by user.")
        console.warning()
        result = -42
        if console.save_log:
            console.capture_stacktrace()
    finally:
        with suppress(KeyboardInterrupt):
            console.save_log_to_file(command)

        console.close()
    return result


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
