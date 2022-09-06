import sys

from .cmdline import parse_cmdline
from .console import Log
from .exceptions import BriefcaseError, HelpText


def main():
    logger = Log()
    command = None
    try:
        command, options = parse_cmdline(sys.argv[1:], logger=logger)
        command.check_obsolete_data_dir()
        command.parse_config("pyproject.toml")
        command(**options)
        result = 0
    except HelpText as e:
        logger.info()
        logger.info(str(e))
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
        if getattr(command, "save_log", False):
            logger.capture_stacktrace()
    finally:
        logger.save_log_to_file(command)

    sys.exit(result)


if __name__ == "__main__":
    main()
