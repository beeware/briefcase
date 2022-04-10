import logging
import sys

from .cmdline import parse_cmdline
from .exceptions import BriefcaseError


class LogFormatter(logging.Formatter):
    base_message = "%(message)s"
    default_format = logging.Formatter(base_message)
    debug_format = logging.Formatter(">>> " + base_message)

    def format(self, record):
        if record.levelno < logging.INFO:
            log_fmt = self.debug_format
        else:
            log_fmt = self.default_format
        return log_fmt.format(record)


def setup_logging(verbosity: int = 1):
    logger = logging.getLogger("briefcase")

    if verbosity > 1:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(LogFormatter())
    console_handler.setLevel(log_level)

    logger.addHandler(console_handler)
    logger.setLevel(log_level)


def main():
    try:
        command, options = parse_cmdline(sys.argv[1:])
        setup_logging(command.verbosity)
        command.parse_config('pyproject.toml')
        command(**options)
        result = 0
    except BriefcaseError as e:
        print(e, file=sys.stdout if e.error_code == 0 else sys.stderr)
        result = e.error_code
    except KeyboardInterrupt:
        print()
        print("Aborted by user.")
        print()
        result = -42

    sys.exit(result)


if __name__ == '__main__':
    main()
