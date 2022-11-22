import re
import signal
from abc import abstractmethod
from typing import Optional

from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError, BriefcaseTestSuiteFailure

from .base import BaseCommand, full_options


class LogFilter:
    DEFAULT_SUCCESS_REGEX = (
        # Unittest
        # The ?P<a...> groups are to support Android logging differences.
        # when https://github.com/chaquo/chaquopy/issues/746 is resolved,
        # those groups can be deleted.
        r"(^-{65,}\n(?P<a1> \n)?Ran \d+ tests in \d+\.\d{3}s"
        r"\n(?P<a2> )?\n(?P<a3> \n)?OK( \(.*\))?$)"
        # PyTest
        r"|"
        r"(^={10,} ("
        r"((\d+ passed)?((, )?\d+ skipped)?(, \d+ warnings?)?)"
        r"|(no tests ran)"
        r") in \d+\.\d+s ={10,}$)"
    )

    DEFAULT_FAILURE_REGEX = (
        # Unittest
        # The ?P<a...> groups are to support Android logging differences.
        # when https://github.com/chaquo/chaquopy/issues/746 is resolved,
        # those groups can be deleted.
        r"(^-{65,}\n(?P<a1> \n)?Ran \d+ tests in \d+\.\d{3}s"
        r"\n(?P<a2> )?\n(?P<a3> \n)?FAILED( \(.*\))?$)"
        # Pytest
        r"|"
        r"(^={10,} ("
        r"(\d+ failed(, \d+ passed)?(, \d+ skipped)?(, \d+ errors?)?)"
        r"|(\d+ errors?)"
        r") in \d+.\d+s ={10,}$)"
    )

    def __init__(
        self,
        log_popen,
        clean_filter,
        clean_output,
        success_filter,
        failure_filter,
    ):
        """Create a filter for a log stream.

        :param log_popen: The Popen object for the stream producing the logs.
        :param clean_filter: A function that will filter a line of logs,
            returning a "clean" line without any log system preamble.
        :param clean_output: Should the output displayed to the user be the
            "clean" output? (Default: True).
        :param success_filter: A function that will operate on a string
            containing the last 10 lines of "clean" (i.e., preamble filtered)
            logs, returning True if a "success" condition has been detected. If
            the success filter returns True, the log process will be terminated.
        :param success_filter: A function that will operate on a string
            containing the last 10 lines of "clean" (i.e., preamble filtered)
            logs, returning True if a "failure" condition has been detected. If
            the failure filter returns True, the log process will be terminated.
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

            # If the clean filter says the line can be dumped, return None
            if filtered is None:
                return None

            # If there's a cleaned line, we can determine if it should be included in analysis
            clean_line, included = filtered
        else:
            # If we don't perform cleaning, we assume all content is potentially
            # Python, and should be included in analysis
            clean_line = line
            display_line = line
            included = True

        # If we're not using clean output, use the raw line for display.
        if self.clean_output:
            display_line = clean_line
        else:
            display_line = line

        # If the line is Python content, append the new line, then clip the
        # recent history to the most recent 10 clean lines, and build a single
        # string that is the tail of the recent clean lines.
        if included:
            self.recent_history.append(clean_line)
            self.recent_history = self.recent_history[-10:]
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
    def test_filter(pattern):
        """A factory method for producing filter functions.

        :param pattern: The multiline regex pattern that identifies success in a log.
        :returns: A log filter function that returns True if the pattern was found
        """
        regex = re.compile(pattern, re.MULTILINE)

        def filter_func(recent):
            return regex.search(recent) is not None

        # Annotate the function with the regex to make it easier to test
        filter_func.__regex__ = regex
        return filter_func


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
        parser.add_argument(
            "--no-auto-update",
            dest="auto_update",
            action="store_false",
            help="Prevent any automated update or build before running.",
        )

    def _prepare_log_stream(self, app: BaseConfig, test_mode: bool):
        """Perform the default setup of a log stream.

        This won't be used by every backend; but it's a sufficiently common
        default that it's been factored out.

        :param app: The app to be launched
        :param test_mode: Are we launching in test mode?
        :returns: A dictionary of additional arguments to pass to the Popen
        """
        if test_mode:
            # In test mode, set a BRIEFCASE_MAIN_MODULE environment variable
            # to override the module at startup
            self.logger.info("Starting test_suite...", prefix=app.app_name)
            return {
                "env": {
                    "BRIEFCASE_MAIN_MODULE": app.main_module(test_mode),
                }
            }
        else:
            self.logger.info("Starting app...", prefix=app.app_name)
            return {}

    def _stream_app_logs(
        self,
        app: BaseConfig,
        popen,
        test_mode=False,
        clean_filter=None,
        clean_output=False,
        stop_func=lambda: False,
        log_stream=False,
    ):
        """Stream the application's logs, monitoring for exit conditions.

        Catches and cleans up after any Ctrl-C interrupts.

        :param app: The app to be launched
        :param popen: The Popen object for the stream we are monitoring
        :param test_mode: Are we launching in test mode?
        :param clean_filter: The log cleaning filter to use; see ``LogFilter``
            for details.
        :param clean_output: Should the cleaned output be presented to the user?
        :param stop_func: (Optional) A function that will be invoked to determine
            if the log stream should be terminated.
        :param log_stream: Is this a log stream, rather than a literal app stream?
            On some platforms (especially mobile), we monitor a log stream,
            rather that the output of the app itself. If this case, the cleanup
            process is different, as the reported exit status of the popen object
            is of the log, not the app itself.
        """
        try:
            if test_mode:
                success_filter = LogFilter.test_filter(
                    getattr(app, "test_success_regex", LogFilter.DEFAULT_SUCCESS_REGEX)
                )
                failure_filter = LogFilter.test_filter(
                    getattr(app, "test_failure_regex", LogFilter.DEFAULT_FAILURE_REGEX)
                )
            else:
                success_filter = None
                failure_filter = None

            log_filter = LogFilter(
                popen,
                clean_filter=clean_filter,
                clean_output=clean_output,
                success_filter=success_filter,
                failure_filter=failure_filter,
            )

            # Start streaming logs for the app.
            self.logger.info("=" * 75)
            self.tools.subprocess.stream_output(
                label="log stream" if log_stream else app.app_name,
                popen_process=popen,
                stop_func=stop_func,
                filter_func=log_filter,
            )

            # If we're in test mode, and log streaming ends,
            # check for the status of the test suite.
            if test_mode:
                if log_filter.success:
                    self.logger.info("Test suite passed!", prefix=app.app_name)
                else:
                    if log_filter.success is None:
                        raise BriefcaseCommandError(
                            "Test suite didn't report a result."
                        )
                    else:
                        self.logger.error("Test suite failed!", prefix=app.app_name)
                        raise BriefcaseTestSuiteFailure()
            elif not log_stream:
                # If we're monitoring an actual app (not just a log stream),
                # and the app didn't exit cleanly, surface the error to the user.
                if popen.returncode != 0:
                    raise BriefcaseCommandError(f"Problem running app {app.app_name}.")

        except KeyboardInterrupt:
            pass  # Catch CTRL-C to exit normally

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
        auto_update: Optional[bool] = True,
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
        if (
            (not template_file.exists())  # App hasn't been created
            or update  # An explicit update has been requested
            or (not binary_file.exists())  # Binary doesn't exist yet
            or (test_mode and auto_update)  # Test mode, and update hasn't been disabled
        ):
            state = self.build_command(
                app,
                update=update,
                test_mode=test_mode,
                **options,
            )
        else:
            state = None

        self.verify_app_tools(app)

        state = self.run_app(app, test_mode=test_mode, **full_options(state, options))

        return state
