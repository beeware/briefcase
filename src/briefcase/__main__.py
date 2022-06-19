import subprocess
import sys

from .cmdline import parse_cmdline
from .console import Log
from .exceptions import BriefcaseError, HelpText
from .integrations.subprocess import log_command, log_output, log_return_code


def main():
    try:
        log = Log()
        command, options = parse_cmdline(sys.argv[1:])
        log = command.logger
        command.parse_config("pyproject.toml")
        command(**options)
        result = 0
    except HelpText as e:
        log.info()
        log.info(str(e))
        result = e.error_code
    except BriefcaseError as e:
        log_subprocess(log, e)
        log.error()
        log.error(str(e))
        result = e.error_code
    except KeyboardInterrupt:
        log.warning()
        log.warning("Aborted by user.")
        log.warning()
        result = -42

    sys.exit(result)


def log_subprocess(log, e):
    """If e is a CalledProcessError, or is directly or indirectly caused by
    one, log the details of the subprocess."""
    if log.verbosity >= log.DEBUG:
        return  # Everything's already been logged.

    while e:
        if isinstance(e, subprocess.CalledProcessError):
            log_command(log, "info", e.cmd)
            log_output(log, "info", e.output, e.stderr)
            log_return_code(log, "info", e.returncode)
            break
        e = e.__cause__ or e.__context__


if __name__ == "__main__":
    main()
