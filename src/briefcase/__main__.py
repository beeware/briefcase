import sys

from .cmdline import parse_cmdline
from .console import Log
from .exceptions import BriefcaseError, HelpText


def main():
    log = Log()
    command = None
    try:
        command, options = parse_cmdline(sys.argv[1:])
        command.parse_config("pyproject.toml")
        command(**options)
        result = 0
    except HelpText as e:
        log.info()
        log.info(str(e))
        result = e.error_code
    except BriefcaseError as e:
        log.error()
        log.error(str(e))
        result = e.error_code
        log.capture_stacktrace()
    except Exception:
        log.capture_stacktrace()
        raise
    except KeyboardInterrupt:
        log.warning()
        log.warning("Aborted by user.")
        log.warning()
        result = -42
        if getattr(command, "save_log", False):
            log.capture_stacktrace()
    finally:
        log.save_log_to_file(command)

    sys.exit(result)


if __name__ == "__main__":
    main()
