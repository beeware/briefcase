from __future__ import annotations

import logging
import operator
import os
import platform
import re
import sys
import traceback
from contextlib import contextmanager
from datetime import datetime
from enum import IntEnum
from pathlib import Path

from rich.console import Console as RichConsole
from rich.control import strip_control_codes
from rich.highlighter import RegexHighlighter
from rich.markup import escape
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.traceback import Traceback

from briefcase import __version__

# Regex to identify settings likely to contain sensitive information
SENSITIVE_SETTING_RE = re.compile(r"API|TOKEN|KEY|SECRET|PASS|SIGNATURE", flags=re.I)

# 7-bit C1 ANSI escape sequences
ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class InputDisabled(Exception):
    def __init__(self):
        super().__init__(
            "Input is disabled; cannot request user input without a default"
        )


def sanitize_text(text: str) -> str:
    """Remove control codes and ANSI escape sequences from a line of text.

    This is useful for extracting the plain text from the output of third party tools
    that may be including markup for display in the console.
    """
    return ANSI_ESCAPE_RE.sub("", strip_control_codes(text))


class RichConsoleHighlighter(RegexHighlighter):
    """Custom Rich highlighter for printing to the console.

    This highlighter limits text highlighting to only URLs.

    By default, Rich applies several highlighting rules to anything it prints for
    concepts like UUIDs, markup, IP addresses, numbers, etc. All these colorful
    additions to the text can become overbearing and distracting given much of the
    output does not benefit from coloring.

    This defines a visually simpler style that highlights URLs in a way that is vaguely
    consistent with a default HTML stylesheet, but otherwise renders content as-is.
    """

    base_style = "repr."
    highlights = [r"(?P<url>(file|https|http|ws|wss)://[-0-9a-zA-Z$_+!`(),.?/;:&=%#]*)"]


class Printer:
    """Interface for printing and managing output to the console and/or log."""

    def __init__(self, log_width=180):
        """Create an interface for printing and managing output to the console and/or
        log.

        The default width is wide enough to render the output of ``sdkmanager
        --list_installed`` without line wrapping.

        :param width: The width at which content should be wrapped.
        """
        self.log_width = log_width

        # A wrapper around the console
        self.console = RichConsole(
            highlighter=RichConsoleHighlighter(),
            emoji=False,
            soft_wrap=True,
        )

        # Rich only records what's being logged if it is actually written somewhere;
        # writing to /dev/null allows Rich to do so without needing to print the
        # logs in the console or save them to file before it is known a file is
        # wanted.
        self.dev_null = open(os.devnull, "w", encoding="utf-8", errors="ignore")
        self.log = RichConsole(
            file=self.dev_null,
            record=True,
            width=self.log_width,
            force_interactive=False,
            force_terminal=False,
            no_color=True,
            color_system=None,
            markup=False,
            emoji=False,
            highlight=False,
            soft_wrap=True,
        )

    def __del__(self):
        self.dev_null.close()

    def __call__(self, *messages, stack_offset=5, show=True, **kwargs):
        """Entry point for all printing to the console and the log.

        The log records all content that is printed whether it is shown in the console
        or not (e.g. debug output). When execution completes, the log is conditionally
        exported and saved to a file.

        :param messages: content to print and/or log
        :param show: True (default) to print and log messages; False to only log.
        :param stack_offset: number of levels up the stack where logging was invoked.
            This tells Rich the number of levels to recurse up the stack to find the
            filename to put in the right column of the Rich log. Defaults to 5 since
            most uses are 5 levels deep from the actual logging.
        """
        if show:
            self.to_console(*messages, **kwargs)
        self.to_log(*messages, stack_offset=stack_offset, **kwargs)

    def to_console(self, *messages, **kwargs):
        """Write only to the console and skip writing to the log."""
        self.console.print(*messages, **kwargs)

    def to_log(self, *messages, stack_offset=5, **kwargs):
        """Write only to the log and skip writing to the console."""
        self.log.log(
            *map(sanitize_text, messages), _stack_offset=stack_offset, **kwargs
        )

    def export_log(self):
        """Export the text of the entire log; the log is also cleared."""
        return self.log.export_text()


class RichLoggingStream:
    """Stream for logging.StreamHandler that prints to console via debug logging."""

    def __init__(self, logger: Log):
        self.logger = logger

    def write(self, msg: str) -> None:
        self.logger.debug(msg)


class RichLoggingHandler(logging.StreamHandler):
    """A debug handler for third party tools using stdlib logging."""

    def __init__(self, stream: RichLoggingStream):
        super().__init__(stream=stream)
        self.setLevel(logging.DEBUG)
        self.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))


class LogLevel(IntEnum):
    INFO = 0
    VERBOSE = 1
    DEBUG = 2
    DEEP_DEBUG = 3


class Log:
    """Manage logging output driven by verbosity flags."""

    # subdirectory of command.base_path to store log files
    LOG_DIR = "logs"

    def __init__(self, printer=None, verbosity: LogLevel = LogLevel.INFO):
        self.print = Printer() if printer is None else printer
        # --verbosity flag: 0 for info, 1 for debug, 2 for deep debug
        self.verbosity = verbosity
        # --log flag to force logfile creation
        self.save_log = False
        # flag set by exceptions to skip writing the log; save_log takes precedence.
        self.skip_log = False
        # Rich stacktraces of exceptions for logging to file.
        # A list of tuples containing a label for the thread context, and the Trace object
        self.stacktraces = []
        # functions to run for additional logging if creating a logfile
        self.log_file_extras = []
        # The current context for the log
        self._context = ""

    @contextmanager
    def context(self, context):
        """Wrap a collection of output in a logging context.

        A logging context is a prefix on every logging line. It is used when a set of
        commands (and output) is being run in a very specific way that needs to be
        highlighted, such as running a command in a Docker container.

        :param context: The name of the context to enter. This *must* be simple text,
            with no markup or other special characters.
        """
        self.info()
        self.info(f"Entering {context} context...")
        old_context = self._context
        self._context = f"{context}| "
        self.info("-" * (72 - len(context)))
        try:
            yield
        finally:
            self.info("-" * (72 - len(context)))
            self._context = old_context
            self.info(f"Leaving {context} context.")
            self.info()

    def _log(
        self,
        preface="",
        prefix="",
        message="",
        show=True,
        markup=False,
        style=None,
    ):
        """Funnel to log all messages.

        :param preface: value to be printed on the far left of the message and symbolic
            of the type of message being printed.
        :param prefix: text prepended to the message wrapped in brackets and will be
            presented as dimmer compared to the styling of the message text.
        :param message: text to log; can contain Rich tags if markup=True.
        :param show: True to print message to console; False to not print it. This is to
            allow logs to be saved to a file without printing them.
        :param markup: whether to interpret Rich markup in the prefix, preface, and
            message; if True, all text must already be escaped; defaults False.
        :param style: Rich style to apply to everything printed for message.
        """
        if not message:
            # When a message is not provided, only output the context;
            # This type of call is just clearing some vertical space.
            self.print(self._context, show=show)
        else:
            if prefix:
                # insert vertical space before for all messages with a prefix
                self.print(self._context, show=show)
                if not markup:
                    preface, prefix, message = (
                        escape(text) for text in (preface, prefix, message)
                    )
                prefix = f"[dim]\\[{prefix}][/dim] "
                markup = True
            for line in message.splitlines():
                self.print(
                    f"{self._context}{preface}{prefix}{line}",
                    show=show,
                    markup=markup,
                    style=style,
                )

    def debug(self, message="", *, preface="", prefix="", markup=False):
        """Log messages at debug level; included if verbosity >= 2."""
        self._log(
            preface=preface,
            prefix=prefix,
            message=message,
            show=self.is_debug,
            markup=markup,
            style="dim",
        )

    def verbose(self, message="", *, prefix="", markup=False):
        """Log message at verbose level if debug enabled; included if verbosity >= 1."""
        self._log(prefix=prefix, message=message, show=self.is_verbose, markup=markup)

    def info(self, message="", *, prefix="", markup=False):
        """Log message at info level; always included in output."""
        self._log(prefix=prefix, message=message, markup=markup)

    def warning(self, message="", *, prefix="", markup=False):
        """Log message at warning level; always included in output."""
        self._log(prefix=prefix, message=message, markup=markup, style="bold yellow")

    def error(self, message="", *, prefix="", markup=False):
        """Log message at error level; always included in output."""
        self._log(prefix=prefix, message=message, markup=markup, style="bold red")

    @property
    def verbosity(self) -> LogLevel:
        return self._verbosity

    @verbosity.setter
    def verbosity(self, value: int | LogLevel):
        """Clamp verbosity between valid log levels."""
        self._verbosity = LogLevel(max(min(LogLevel), min(value, max(LogLevel))))

    @property
    def is_verbose(self):
        """Is verbose logging enabled via the -v flag?

        This includes Briefcase logging that isn't relevant during normal operation.
        """
        return self.verbosity >= LogLevel.VERBOSE

    @property
    def is_debug(self):
        """Is debug logging enabled via the -vv flag?

        This includes debug logging from third party tools.
        """
        return self.verbosity >= LogLevel.DEBUG

    @property
    def is_deep_debug(self):
        """Is deep debug logging enabled via the -vvv flag?

        This includes debug logging from third party tools.
        """
        return self.verbosity >= LogLevel.DEEP_DEBUG

    def configure_stdlib_logging(self, logger_name: str):
        """Configure stdlib logging for a third party tool to log through Rich.

        When a third party tool written in Python uses the stdlib logging for their
        logging, it may provide an abstraction to enable the logging in the console or
        may require a handler to be added externally. Either way, the default handler
        to write to the console, i.e. logging.StreamHandler, will bypass Rich logging
        and therefore not be included in the logfile. To avoid this issue, this will
        add a handler that specifically writes to the console through Rich.

        :param logger_name: Name of the logger the third party tool uses. Typically,
            this is the package name or path to a submodule for the package. Since
            logging uses namespaces for logging, enabling DEBUG logging for `git` will
            also enable it for others like `git.cmd`, `git.remote`, `git.config`, etc.
        """
        if not self.is_deep_debug:
            return

        logger = logging.getLogger(logger_name)

        # do not add another rich handler if one already exists
        if not any(isinstance(h, RichLoggingHandler) for h in logger.handlers):
            logger.addHandler(RichLoggingHandler(stream=RichLoggingStream(logger=self)))
            logger.setLevel(logging.DEBUG)

    def capture_stacktrace(self, label="Main thread"):
        """Preserve Rich stacktrace from exception while in except block.

        :param label: An identifying label for the thread that has raised the
            stacktrace. Defaults to the main thread.
        """
        exc_info = sys.exc_info()
        try:
            self.skip_log = exc_info[1].skip_logfile
        except AttributeError:
            pass

        self.stacktraces.append((label, Traceback.extract(*exc_info, show_locals=True)))

    def add_log_file_extra(self, func):
        """Register a function to be called in the event that a log file is written.

        This can be used to provide additional debugging information which is too
        expensive to gather pre-emptively.
        """
        self.log_file_extras.append(func)

    def save_log_to_file(self, command):
        """Save the current application log to file."""
        # A log file is always written if a Command ran and `--log` was provided.
        # If `--log` was not provided, then the log is written when an exception
        # occurred and the exception was not explicitly configured to skip the log.
        if not (
            command and (self.save_log or (self.stacktraces and not self.skip_log))
        ):
            return

        with command.input.wait_bar("Saving log...", transient=True):
            self.print.to_console()
            log_filename = f"briefcase.{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.{command.command}.log"
            log_filepath = command.base_path / self.LOG_DIR / log_filename
            try:
                log_filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(
                    log_filepath, "w", encoding="utf-8", errors="backslashreplace"
                ) as log_file:
                    log_file.write(self._build_log(command))
            except OSError as e:
                self.error(f"Failed to save log to {log_filepath}: {e}")
            else:
                self.warning(f"Log saved to {log_filepath}")
            self.print.to_console()

    def _build_log(self, command):
        """Accumulate all information to include in the log file."""
        # add the exception stacktrace to end of log if one was captured
        if self.stacktraces:
            # using print.log.print() instead of print.to_log() to avoid
            # timestamp and code location inclusion for the stacktrace box.
            for thread, stacktrace in self.stacktraces:
                self.print.log.print(
                    f"{thread} traceback:",
                    Traceback(
                        trace=stacktrace,
                        width=self.print.log_width,
                        show_locals=True,
                    ),
                    new_line_start=True,
                )

        if self.log_file_extras:
            with command.input.wait_bar(
                "Collecting extra information for log...",
                transient=True,
            ):
                self.debug()
                self.debug("Extra information:")
                for func in self.log_file_extras:
                    try:
                        func()
                    except Exception:
                        self.error(traceback.format_exc())

        # build log header and export buffered log from Rich
        uname = platform.uname()
        sanitized_env_vars = "\n".join(
            f"\t{env_var}={value if not SENSITIVE_SETTING_RE.search(env_var) else '********************'}"
            for env_var, value in sorted(command.tools.os.environ.items())
        )
        return (
            f"Date/Time:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
            f"Command line:    {' '.join(sys.argv)}\n"
            f"\n"
            f"OS Release:      {uname.system} {uname.release}\n"
            f"OS Version:      {uname.version}\n"
            f"Architecture:    {uname.machine}\n"
            f"Platform:        {platform.platform(aliased=True)}\n"
            f"\n"
            f"Python exe:      {sys.executable}\n"
            # replace line breaks with spaces (use chr(10) since '\n' isn't allowed in f-strings...)
            f"Python version:  {sys.version.replace(chr(10), ' ')}\n"
            # sys.real_prefix was used in older versions of virtualenv.
            # sys.base_prefix is always the python exe's original site-specific directory (e.g. /usr/local).
            # sys.prefix is updated (from base_prefix's value) to the virtual env's site-specific directory.
            f"Virtual env:     {hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix}\n"
            # for conda, prefix and base_prefix are likely the same but contain a conda-meta dir.
            f"Conda env:       {(Path(sys.prefix) / 'conda-meta').exists()}\n"
            f"\n"
            f"Briefcase:       {__version__}\n"
            f"Target platform: {command.platform}\n"
            f"Target format:   {command.output_format}\n"
            f"\n"
            f"Environment Variables:\n"
            f"{sanitized_env_vars}\n"
            f"\n"
            f"Briefcase Log:\n"
            f"{self.print.export_log()}"
        )


class Console:
    def __init__(self, printer=None, enabled=True):
        self.enabled = enabled
        self.print = Printer() if printer is None else printer
        # Use Rich's input() to read from user
        self.input = self.print.console.input
        self._wait_bar: Progress = None
        # Signal that Rich is dynamically controlling the console output. Therefore,
        # all output must be printed to the screen by Rich to prevent corruption of
        # dynamic elements like the Wait Bar.
        self.is_console_controlled = False

    @property
    def is_interactive(self):
        """Returns interactivity mode based on the presence of a tty for stdout.

        In a non-interactive session, Rich's dynamic elements like progress bars should
        be disabled. By default, Rich will not render dynamic elements if a tty is not
        available. However, environment variables like FORCE_COLOR can override this
        behavior in Rich to not only show ANSI color and style but also dynamic
        elements. In a CI environment with this configuration, a long-lived progress bar
        can dramatically compromise the quality of logged output. So, dynamic elements
        should be specifically disabled in non-interactive sessions.
        """
        return sys.stdout.isatty()

    def progress_bar(self):
        """Returns a progress bar as a context manager."""
        return Progress(
            TextColumn("  "),
            SpinnerColumn("line", speed=1.5, style="default"),
            BarColumn(bar_width=50),
            TextColumn("{task.percentage:>3.1f}%", style="default"),
            TextColumn("•", style="default"),
            TimeRemainingColumn(compact=True, elapsed_when_finished=True),
            disable=not self.is_interactive,
            console=self.print.console,
        )

    @contextmanager
    def wait_bar(
        self,
        message="",
        done_message="done",
        *,
        transient=False,
        markup=False,
    ):
        """Activates the Wait Bar as a context manager.

        If the Wait Bar is already active, then its message is updated for the new
        context. Once the new context is complete, the previous Wait Bar message
        is restored.

        :param message: text explaining what is being awaited; should end in '...'
        :param done_message: text appended to the message after exiting
        :param transient: if True, remove bar and message from screen after exiting;
            if False (default), the message will remain on the screen without pulsing bar.
        :param markup: whether to interpret Rich styling markup in the message; if True,
            the message must already be escaped; defaults False.
        """
        if self._wait_bar is None:
            self._wait_bar = Progress(
                TextColumn("    "),
                BarColumn(bar_width=20, style="black", pulse_style="white"),
                TextColumn("{task.fields[message]}"),
                transient=True,
                disable=not self.is_interactive,
                console=self.print.console,
            )
            # start=False causes the progress bar to "pulse"
            # message=None is a sentinel the Wait Bar should be inactive
            self._wait_bar.add_task("", start=False, message=None)

        self.is_console_controlled = True
        wait_bar_task = self._wait_bar.tasks[0]
        previous_message = wait_bar_task.fields["message"]
        self._wait_bar.update(wait_bar_task.id, message=message)
        try:
            self._wait_bar.start()
            yield
        except BaseException:
            # ensure the message is left on the screen even if user sends CTRL+C
            if message and not transient:
                self.print(message, markup=markup)
            raise
        else:
            if message and not transient:
                self.print(f"{message} {done_message}", markup=markup)
        finally:
            self._wait_bar.update(wait_bar_task.id, message=previous_message)
            # Deactivate the Wait Bar if returning to its initial state
            if previous_message is None:
                self._wait_bar.stop()
                self.is_console_controlled = False

    @contextmanager
    def release_console_control(self):
        """Context manager to remove console elements such as the Wait Bar.

        This is useful to temporarily release control of the console when, e.g., a
        process is interrupted or a user needs to be prompted. For instance, when batch
        scripts are interrupted by CTRL+C in cmd.exe, the user may be prompted to abort
        the script; so, the console cannot be controlled while such scripts run or the
        prompt may be hidden from the user.
        """
        # Preserve current console state
        is_output_controlled = self.is_console_controlled
        is_wait_bar_running = self._wait_bar and self._wait_bar.live.is_started

        # Stop any active dynamic console elements
        if is_wait_bar_running:
            self._wait_bar.stop()

        self.is_console_controlled = False
        try:
            yield
        finally:
            self.is_console_controlled = is_output_controlled
            # Restore previous console state
            if is_wait_bar_running:
                self._wait_bar.start()

    def prompt(self, *values, markup=False, **kwargs):
        """Print to the screen for soliciting user interaction.

        :param values: strings to print as the user prompt
        :param markup: True if prompt contains Rich markup
        """
        if self.enabled:
            self.print(*values, markup=markup, stack_offset=4, **kwargs)

    def boolean_input(self, question, default=False):
        """Get a boolean input from user, in the form of y/n.

        The user might press "y" for true or "n" for false. If input is disabled,
        returns default. If input is disabled and default is *not* defined,
        InputDisabled is raised.

        :param question: A string message specifying the question to be answered by the
            user.
        :param default: (optional) Default response (True/False)
        :returns: True if the user selected "y", or False if they selected "n".
        """
        if default is None:
            yes_no = "y/n"
            default_text = None
        elif default:
            yes_no = "[Y/n]"
            default_text = "y"
        else:
            yes_no = "[y/N]"
            default_text = "n"

        prompt = f"{question} {yes_no}? "

        result = self.selection_input(
            prompt=prompt,
            choices=["y", "n"],
            default=default_text,
            error_message="Please enter Y or N",
            transform=lambda s: s.lower()[:1],
        )
        if result == "y":
            return True

        return False

    def selection_input(
        self,
        prompt,
        choices,
        default=None,
        error_message="Invalid Selection",
        transform=None,
    ):
        """Prompt the user to select an option from a list of choices.

        :param prompt: The text prompt to display
        :param choices: The list of available choices
        :param default: The default choice to select. If None,
        :param error_message: The error message to display to the user.
        :param transform: The text transform to apply to any user input before
            performing any validity checks.
        """
        while True:
            result = self.text_input(prompt, default)

            if transform is not None and result is not None:
                result = transform(result)

            if result in choices:
                return result

            self.prompt()
            self.prompt(error_message)

    def text_input(self, prompt, default=None):
        """Prompt the user for text input.

        If no default is specified, the input will be returned as entered.

        The default will also be returned if input is disabled. If input is disabled,
        and there is no default, InputDisabled will be raised.

        :param prompt: The prompt to display to the user.
        :param default: (optional) The response to return if the user provides no input.
        :returns: The content entered by the user.
        """
        try:
            user_input = self(prompt)
            if default is not None and user_input == "":
                return default
        except InputDisabled:
            if default is not None:
                return default
            raise

        return user_input

    def __call__(self, prompt, *, markup=False):
        """Present input() interface."""
        if not self.enabled:
            raise InputDisabled()

        # make the prompt *bold* if it doesn't already contain markup
        escaped_prompt = f"[bold]{escape(prompt)}[/bold]" if not markup else prompt

        try:
            input_value = self.input(escaped_prompt, markup=True)
        except EOFError:
            raise KeyboardInterrupt

        self.print.to_log(prompt)
        self.print.to_log(f"User input: {input_value}")

        return input_value


def select_option(options, input, prompt="> ", error="Invalid selection", default=None):
    """Prompt the user for a choice from a list of options.

    The options are provided as a dictionary; the values are the human-readable options,
    and the keys are the values that will be returned as the selection. The human-
    readable options will be sorted before display to the user.

    This method does *not* print a question or any leading text; it only prints the list
    of options, and prompts the user for their choice. If the user chooses an invalid
    selection (either provides non-integer input, or an invalid integer), it prints an
    error message and prompts the user again.

    :param options: A dictionary, or list of tuples, of options to present to the user.
    :param input: The function to use to retrieve the user's input. This exists so that
        the user's input can be easily mocked during testing.
    :param prompt: The prompt to display to the user.
    :param error: The error message to display when the user provides invalid input.
    :param default: The default option for empty user input. The options for the user
        start numbering at 1; so, to default to the first item, this should be "1".
    :returns: The key corresponding to the user's chosen option.
    """
    if isinstance(options, dict):
        ordered = list(sorted(options.items(), key=operator.itemgetter(1)))
    else:
        ordered = options

    if input.enabled:
        for i, (key, value) in enumerate(ordered, start=1):
            input.prompt(f"  {i}) {value}")

        input.prompt()

    choices = [str(index) for index in range(1, len(ordered) + 1)]
    index = input.selection_input(
        prompt=prompt, choices=choices, error_message=error, default=default
    )
    return ordered[int(index) - 1][0]
