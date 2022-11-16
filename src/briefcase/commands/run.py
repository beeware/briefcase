import re
import signal
from abc import abstractmethod
from typing import Optional

from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand, full_options


class LogFilter:
    def __init__(
        self,
        log_popen,
        clean_filter=None,
        clean_output=True,
        success_filter=None,
        failure_filter=None,
    ):
        """Create a filter for a log stream.

        :param log_popen: The Popen object for the stream producing the logs.
        :param clean_filter: (Optional) A function that will filter a line of
            logs, returning a "clean" line without any log system preamble.
        :param clean_output: Should the output displayed to the user be the
            "clean" output? (Default: True).
        :param success_filter: (Optional) A function that will operate on a
            string containing the last 5 lines of "clean" (i.e., preamble
            filtered) logs, returning True if a "success" condition has been
            detected. If the success filter returns True, the log process will
            be terminated.
        :param success_filter: (Optional) A function that will operate on a
            string containing the last 5 lines of "clean" (i.e., preamble
            filtered) logs, returning True if a "failure" condition has been
            detected. If the failure filter returns True, the log process will
            be terminated.
        """
        self.log_popen = log_popen
        self.success = None
        self.clean_filter = clean_filter
        self.clean_output = clean_output

        self.recent_history = []
        self.success_filter = success_filter
        self.failure_filter = failure_filter

    def __call__(self, line):
        """Filter a single line of a log.

        :param line: A single line of raw system log content, including the newline.
        """
        # Compute the clean line
        if self.clean_filter:
            filtered = self.clean_filter(line)

            # If the clean line says the line can be ignored for logging purposes,
            # return None to avoid logging the line.
            if filtered is None:
                return None

            # If there's a cleaned line, we can determine if it's Python content.
            clean_line, is_python = filtered
        else:
            # If we don't perform cleaning, we assume all content is potentially Python.
            clean_line = line
            display_line = line
            is_python = True

        # If we're not using clean output, revert the display line to the raw line.
        if self.clean_output:
            display_line = clean_line
        else:
            display_line = line

        # If the line is Python content, clip the recent history to the most
        # recent 4 clean lines, then append the new line, and build a single
        # string that is the tail of the recent clean lines.
        if is_python:
            self.recent_history = self.recent_history[1:5]
            self.recent_history.append(clean_line)
            tail = "\n".join(self.recent_history)

            # Look for the success/failure conditions in the tail
            if self.failure_filter and self.failure_filter(tail):
                self.success = False
                self.log_popen.send_signal(signal.SIGINT)
            elif self.success_filter and self.success_filter(tail):
                self.success = True
                self.log_popen.send_signal(signal.SIGINT)

        # Return the display line
        return display_line

    @staticmethod
    def test_suite_success(pattern):
        """A factory method for producing success filter functions.

        :param pattern: The multiline regex pattern that identifies success in a
            log. If none falls
        :returns: A log filter function that identifies success, based on the
        """
        DEFAULT_SUCCESS_REGEX = (
            # Unittest
            r"(^-{65,}\n)Ran \d+ tests in \d+\.\d{3}s\n\nOK( \(.*\))?"
            # PyTest
            r"|(^={10,}( \d+ passed(, \d+ skipped)?)|(no tests ran) in \d+\.\d+s ={10,}$)"
        )
        success_regex = re.compile(
            pattern if pattern else DEFAULT_SUCCESS_REGEX, re.MULTILINE
        )

        def success_filter(recent):
            return success_regex.search(recent) is not None

        return success_filter

    @staticmethod
    def test_suite_failure(pattern):
        DEFAULT_FAILURE_REGEX = (
            # Unittest
            r"(^-{65,}\n)Ran \d+ tests in \d+\.\d{3}s\n\nFAILED( \(.*\))?"
            # Pytest
            r"|(^={10,} ((\d+ failed(, \d+ passed)?(, \d+ skipped)?)|(\d+ errors?)) in \d+.\d+s ={10,}$)"
        )
        failure_regex = re.compile(
            pattern if pattern else DEFAULT_FAILURE_REGEX, re.MULTILINE
        )

        def failure_filter(recent):
            return failure_regex.search(recent) is not None

        return failure_filter


class RunCommand(BaseCommand):
    command = "run"

    def add_options(self, parser):
        parser.add_argument(
            "-a",
            "--app",
            dest="appname",
            help="The app to run",
        )
        parser.add_argument(
            "-u",
            "--update",
            action="store_true",
            help="Update the app before execution",
        )
        parser.add_argument(
            "--test",
            dest="test_mode",
            action="store_true",
            help="Run the app in test mode",
        )

    @abstractmethod
    def run_app(self, app: BaseConfig, **options):
        """Start an application.

        :param app: The application to start
        """
        ...

    def __call__(
        self,
        appname: Optional[str] = None,
        update: Optional[bool] = False,
        test_mode: Optional[bool] = False,
        **options,
    ):
        # Confirm all required tools are available
        self.verify_tools()

        # Which app should we run? If there's only one defined
        # in pyproject.toml, then we can use it as a default;
        # otherwise look for a -a/--app option.
        if len(self.apps) == 1:
            app = list(self.apps.values())[0]
        elif appname:
            try:
                app = self.apps[appname]
            except KeyError as e:
                raise BriefcaseCommandError(
                    f"Project doesn't define an application named '{appname}'"
                ) from e
        else:
            raise BriefcaseCommandError(
                "Project specifies more than one application; use --app to specify which one to start."
            )
        template_file = self.bundle_path(app)
        binary_file = self.binary_path(app)
        if not template_file.exists():
            state = self.create_command(app, test_mode=test_mode, **options)
            state = self.build_command(
                app,
                test_mode=test_mode,
                **full_options(state, options),
            )
        elif update or test_mode:
            state = self.update_command(app, test_mode=test_mode, **options)
            state = self.build_command(
                app,
                test_mode=test_mode,
                **full_options(state, options),
            )
        elif not binary_file.exists():
            state = self.build_command(app, test_mode=test_mode, **options)
        else:
            state = None

        self.verify_app_tools(app)

        state = self.run_app(app, test_mode=test_mode, **full_options(state, options))

        return state
