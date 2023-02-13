import re
from abc import abstractmethod
from typing import List, Optional

from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError, BriefcaseTestSuiteFailure
from briefcase.integrations.subprocess import StopStreaming

from .base import BaseCommand, full_options


class LogFilter:
    DEFAULT_EXIT_REGEX = r"^>>>>>>>>>> EXIT (?P<returncode>.*) <<<<<<<<<<$"

    def __init__(
        self,
        log_popen,
        clean_filter,
        clean_output,
        exit_filter,
    ):
        """Create a filter for a log stream.

        :param log_popen: The Popen object for the stream producing the logs.
        :param clean_filter: A function that will filter a line of logs,
            returning a "clean" line without any log system preamble.
        :param clean_output: Should the output displayed to the user be the
            "clean" output? (Default: True).
        :param exit_filter: A function that will operate on a string containing
            the last 10 lines of "clean" (i.e., preamble filtered) logs,
            returning the integer exit status of the process if an exit
            condition has been detected, or None if the log stream should
            continue.
        """
        self.log_popen = log_popen
        self.returncode = None
        self.clean_filter = clean_filter
        self.clean_output = clean_output

        self.recent_history = []
        self.exit_filter = exit_filter

    def __call__(self, line):
        """Filter a single line of a log.

        :param line: A single line of raw system log content, including the newline.
        """
        # Compute the clean line
        if self.clean_filter:
            filtered = self.clean_filter(line)

            # If the clean filter says the line can be dumped, return without yielding
            if filtered is None:
                return

            # If there's a cleaned line, we can determine if it should be included in analysis
            clean_line, included = filtered
        else:
            # If we don't perform cleaning, we assume all content is potentially
            # Python, and should be included in analysis
            clean_line = line
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

            # Look for the exit condition in the tail
            if self.exit_filter:
                self.returncode = self.exit_filter(tail)
                if self.returncode is not None:
                    raise StopStreaming()

        # Return the display line
        yield display_line

    @staticmethod
    def test_filter(pattern):
        """A factory method for producing filter functions.

        :param pattern: The multiline regex pattern that identifies content of
            interest in a log (e.g., success/failure conditions)
        :returns: A log filter function that returns True if the pattern was
            found
        """

        def filter_func(recent):
            match = filter_func.regex.search(recent)
            if match:
                try:
                    return int(match.groupdict()["returncode"])
                except KeyError:
                    # No returncode group in regex
                    return -998
                except ValueError:
                    # Non-integer return code content
                    return -999
            return None

        # Annotate the function with the regex that will be used in the function.
        filter_func.regex = re.compile(pattern, re.MULTILINE)
        return filter_func


class RunAppMixin:
    """A mixin that captures the logic of starting an app and streaming the app logs."""

    allows_passthrough = True

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
            exit_filter = LogFilter.test_filter(
                getattr(app, "exit_regex", LogFilter.DEFAULT_EXIT_REGEX)
            )

            log_filter = LogFilter(
                popen,
                clean_filter=clean_filter,
                clean_output=clean_output,
                exit_filter=exit_filter,
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
                if log_filter.returncode == 0:
                    self.logger.info("Test suite passed!", prefix=app.app_name)
                else:
                    if log_filter.returncode is None:
                        raise BriefcaseCommandError(
                            "Test suite didn't report a result."
                        )
                    else:
                        self.logger.error("Test suite failed!", prefix=app.app_name)
                        raise BriefcaseTestSuiteFailure()
            elif log_stream:
                # If we're monitoring a log stream, and the log stream reported a
                # non-zero exit code, surface that error to the user.
                if log_filter.returncode is not None and log_filter.returncode != 0:
                    raise BriefcaseCommandError(f"Problem running app {app.app_name}.")
            else:
                # If we're monitoring an actual app (not just a log stream),
                # and the app didn't exit cleanly, surface the error to the user.
                if popen.returncode != 0:
                    raise BriefcaseCommandError(f"Problem running app {app.app_name}.")

        except KeyboardInterrupt:
            pass  # Catch CTRL-C to exit normally


class RunCommand(RunAppMixin, BaseCommand):
    command = "run"
    description = "Run an app."

    def add_options(self, parser):
        parser.add_argument(
            "-a",
            "--app",
            dest="appname",
            help="The app to run",
        )

        self._add_update_options(parser, context_label=" before running")
        self._add_test_options(parser, context_label="Run")

    def _prepare_app_env(self, app: BaseConfig, test_mode: bool):
        """Prepare the environment for running an app as a log stream.

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

    @abstractmethod
    def run_app(self, app: BaseConfig, **options):
        """Start an application.

        :param app: The application to start
        """
        ...

    def __call__(
        self,
        appname: Optional[str] = None,
        update: bool = False,
        update_requirements: bool = False,
        update_resources: bool = False,
        no_update: bool = False,
        test_mode: bool = False,
        passthrough: Optional[List[str]] = None,
        **options,
    ):
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

        # Confirm host compatibility, that all required tools are available,
        # and that the app configuration is finalized.
        self.finalize(app)

        template_file = self.bundle_path(app)
        binary_file = self.binary_path(app)
        if (
            (not template_file.exists())  # App hasn't been created
            or update  # An explicit update has been requested
            or update_requirements  # An explicit update of requirements has been requested
            or update_resources  # An explicit update of resources has been requested
            or (not binary_file.exists())  # Binary doesn't exist yet
            or (
                test_mode and not no_update
            )  # Test mode, but updates have not been disabled
        ):
            state = self.build_command(
                app,
                update=update,
                update_requirements=update_requirements,
                update_resources=update_resources,
                no_update=no_update,
                test_mode=test_mode,
                **options,
            )
        else:
            state = None

        self.verify_app_tools(app)

        state = self.run_app(
            app,
            test_mode=test_mode,
            passthrough=[] if passthrough is None else passthrough,
            **full_options(state, options),
        )

        return state
