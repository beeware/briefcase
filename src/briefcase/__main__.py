import sys

from .cmdline import parse_cmdline
from .console import Log
from .exceptions import BriefcaseError


def main():
    try:
        log = Log()
        command, options = parse_cmdline(sys.argv[1:])
        command.parse_config("pyproject.toml")
        command(**options)
        result = 0
    except BriefcaseError as e:
        log.error()
        log.error(str(e))
        result = e.error_code
    except KeyboardInterrupt:
        log.warning()
        log.warning("Aborted by user.")
        log.warning()
        result = -42

    sys.exit(result)


if __name__ == "__main__":
    main()
