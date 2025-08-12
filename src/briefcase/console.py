from __future__ import annotations

import logging
import os
import platform
import re
import shutil
import sys
import textwrap
import time
import traceback
from collections.abc import Callable, Iterable, Mapping
from contextlib import contextmanager
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Any

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
from rich.traceback import Trace, Traceback

from briefcase import __version__
from briefcase.config import parse_boolean
from briefcase.exceptions import InputDisabled

# Max width for printing to console; matches argparse's default width
MAX_TEXT_WIDTH = max(min(shutil.get_terminal_size().columns, 80) - 2, 20)

# Regex to identify settings likely to contain sensitive information
SENSITIVE_SETTING_RE = re.compile(r"API|TOKEN|KEY|SECRET|PASS|SIGNATURE", flags=re.I)

# 7-bit C1 ANSI escape sequences
ANSI_ESC_SEQ_RE_DEF = r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
ANSI_ESCAPE_RE = re.compile(ANSI_ESC_SEQ_RE_DEF)


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
    highlights = [
        r"(?P<url>(file|https|http|ws|wss)://[-0-9a-zA-Z$_+!`(),.?/;:&=%#~]*)"
    ]


class RichLoggingStream:
    """Stream for logging.StreamHandler that prints to console via debug logging."""

    def __init__(self, console: Console):
        self.console = console

    def write(self, msg: str) -> None:
        self.console.debug(msg)


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


class NotDeadYet:
    # I’m getting better! No you’re not, you’ll be stone dead in a minute.

    def __init__(self, console: Console):
        """A keep-alive spinner for long-running processes without console output.

        Returned by the Wait Bar's context manager but can be used independently. Use in
        a loop that calls update() each iteration. A keep-alive message will be printed
        every 10 seconds.
        """
        self.console = console
        self.interval_sec: int = 10
        self.message: str = "... still waiting"
        self.ready_time: float = 0.0

        self.reset()  # initialize

    def update(self):
        """Write keep-alive message if the periodic interval has elapsed."""
        if self.ready_time < time.time():
            self.console.print(self.message)
            self.reset()

    def reset(self):
        """Initialize periodic interval to now; next message prints after interval."""
        self.ready_time = time.time() + self.interval_sec


class Console:
    # subdirectory of command.base_path to store log files
    LOG_DIR = "logs"

    def __init__(
        self,
        input_enabled: bool = True,
        verbosity: LogLevel = LogLevel.INFO,
        log_width: int = 180,
    ):
        """Interface for printing and managing output to the console and/or log.

        :param input_enabled: Is the console current enabled for input?
        :param verbosity: Controls how much output is displayed to the user.
        :param log_width: The width at which content should be wrapped in the log file.
            The default width is wide enough to render the output of ``sdkmanager
            --list_installed`` in the log file without line wrapping.
        """
        self.log_width = log_width

        # A wrapper around the console
        self._console_impl = RichConsole(
            highlighter=RichConsoleHighlighter(),
            emoji=False,
            soft_wrap=True,
        )

        # Rich only records what's being logged if it is actually written somewhere;
        # writing to /dev/null allows Rich to do so without needing to print the
        # logs in the console or save them to file before it is known a file is wanted.
        self._dev_null = open(os.devnull, "w", encoding="utf-8", errors="ignore")
        self._log_impl = RichConsole(
            file=self._dev_null,
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

        ##################################################################
        # Logging properties
        ##################################################################

        # --verbosity flag: see LogLevel for valid values
        self.verbosity = verbosity
        # --log flag to force logfile creation
        self.save_log = False
        # flag set by exceptions to skip writing the log; save_log takes precedence.
        self.skip_log = False
        # Rich stacktraces of exceptions for logging to file.
        # A list of tuples containing a label for the thread context, and the Trace object
        self.stacktraces: list[tuple[str, Trace]] = []
        # functions to run for additional logging if creating a logfile
        self.log_file_extras: list[Callable[[], object]] = []
        # The current context for the log
        self._context = ""

        ##################################################################
        # Console management properties
        ##################################################################
        self.input_enabled = input_enabled

        self._wait_bar: Progress | None = None
        # Signal that Rich is dynamically controlling the console output. Therefore,
        # all output must be printed to the screen by Rich to prevent corruption of
        # dynamic elements like the Wait Bar.
        self.is_console_controlled = False

    def close(self):
        self._dev_null.close()
        self._dev_null = None

    def __del__(self):
        if self._dev_null:
            self.close()

    #################################################################
    # Console primitives
    #################################################################

    def print(self, *messages, stack_offset=5, show=True, **kwargs):
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
        self._console_impl.print(*messages, **kwargs)

    def to_log(self, *messages, stack_offset=5, **kwargs):
        """Write only to the log and skip writing to the console."""
        self._log_impl.log(
            *map(sanitize_text, messages), _stack_offset=stack_offset, **kwargs
        )

    def export_log(self):
        """Export the text of the entire log; the log is also cleared."""
        return self._log_impl.export_text()

    #################################################################
    # Logging controls
    #################################################################
    @contextmanager
    def context(self, context: str):
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
        """Log message at verbose level; included if verbosity >= 1."""
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
            logger.addHandler(
                RichLoggingHandler(stream=RichLoggingStream(console=self))
            )
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

    def add_log_file_extra(self, func: Callable[[], object]):
        """Register a function to be called in the event that a log file is written.

        This can be used to provide additional debugging information which is too
        expensive to gather preemptively.
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

        with command.console.wait_bar("Saving log...", transient=True):
            self.to_console()
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
            self.to_console()

    def _build_log(self, command) -> str:
        """Accumulate all information to include in the log file."""
        # Add the exception stacktraces to end of log if any were captured
        if self.stacktraces:
            # using print() instead of to_log() to avoid
            # timestamp and code location inclusion for the stacktrace box.
            for thread, stacktrace in self.stacktraces:
                self._log_impl.print(
                    f"{thread} traceback:",
                    Traceback(
                        trace=stacktrace,
                        width=self.log_width,
                        show_locals=True,
                    ),
                    new_line_start=True,
                )

        # Retrieve additional logging added by the Command
        if self.log_file_extras:
            with self.wait_bar(
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

        # Capture env vars removing any potentially sensitive information
        sanitized_env_vars = "\n".join(
            f"\t{env_var}={value if not SENSITIVE_SETTING_RE.search(env_var) else '********************'}"
            for env_var, value in sorted(command.tools.os.environ.items())
        )

        # Capture pyproject.toml if one exists in the current directory
        try:
            with open(Path.cwd() / "pyproject.toml", encoding="utf-8") as f:
                pyproject_toml = f.read().strip()
        except OSError as e:
            pyproject_toml = str(e)

        # Build log with buffered log from Rich
        uname = platform.uname()
        return (
            f"Date/Time:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
            f"Command line:    {' '.join(sys.argv)}\n"
            "\n"
            f"OS Release:      {uname.system} {uname.release}\n"
            f"OS Version:      {uname.version}\n"
            f"Architecture:    {uname.machine}\n"
            f"Platform:        {platform.platform(aliased=True)}\n"
            "\n"
            f"Python exe:      {sys.executable}\n"
            # replace line breaks with spaces (use chr(10) since '\n' isn't allowed in f-strings...)
            f"Python version:  {sys.version.replace(chr(10), ' ')}\n"
            # sys.real_prefix was used in older versions of virtualenv.
            # sys.base_prefix is always the python exe's original site-specific directory (e.g. /usr/local).
            # sys.prefix is updated (from base_prefix's value) to the virtual env's site-specific directory.
            f"Virtual env:     {hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix}\n"
            # for conda, prefix and base_prefix are likely the same but contain a conda-meta dir.
            f"Conda env:       {(Path(sys.prefix) / 'conda-meta').exists()}\n"
            "\n"
            f"Briefcase:       {__version__}\n"
            f"Target platform: {command.platform}\n"
            f"Target format:   {command.output_format}\n"
            "\n"
            "Environment Variables:\n"
            f"{sanitized_env_vars}\n"
            "\n"
            "pyproject.toml:\n"
            f"{pyproject_toml}\n"
            "\n"
            "Briefcase Log:\n"
            f"{self.export_log()}"
        )

    #################################################################
    # Console controls
    #################################################################

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
        # `sys.__stdout__` is used because Rich captures and redirects `sys.stdout`
        return os.isatty(sys.__stdout__.fileno())

    @property
    def is_color_enabled(self):
        """Is the underlying Rich console using color?

        Rich can be explicitly configured to not use color at Console initialization or
        the NO_COLOR environment variable; alternatively, the derived color system for
        the terminal is influenced by attributes of the platform as well as FORCE_COLOR.
        """
        # no_color has precedence since color_system can be set even if color is disabled
        if self._console_impl.no_color:
            return False
        else:
            return self._console_impl.color_system is not None

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
            console=self._console_impl,
        )

    @contextmanager
    def wait_bar(
        self,
        message: str = "",
        done_message: str = "done",
        *,
        transient: bool = False,
        markup: bool = False,
    ) -> NotDeadYet:
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
        :returns:  Keep-alive spinner to notify user Briefcase is still waiting
        """
        is_wait_bar_disabled = not self.is_interactive
        show_outcome_message = message and (is_wait_bar_disabled or not transient)

        if self._wait_bar is None:
            self._wait_bar = Progress(
                TextColumn("    "),
                BarColumn(bar_width=20, style="black", pulse_style="white"),
                TextColumn("{task.fields[message]}"),
                transient=True,
                disable=is_wait_bar_disabled,
                console=self._console_impl,
            )
            # start=False causes the progress bar to "pulse"
            # message=None is a sentinel the Wait Bar should be inactive
            self._wait_bar.add_task("", start=False, message=None)

        self.print(
            f"{message} started", markup=markup, show=message and is_wait_bar_disabled
        )

        self.is_console_controlled = True
        wait_bar_task = self._wait_bar.tasks[0]
        previous_message = wait_bar_task.fields["message"]
        self._wait_bar.update(wait_bar_task.id, message=message)

        try:
            self._wait_bar.start()
            yield NotDeadYet(console=self)
        except BaseException as e:
            # capture BaseException so message is left on the screen even if user sends CTRL+C
            error_message = "aborted" if isinstance(e, KeyboardInterrupt) else "errored"
            self.print(
                f"{message} {error_message}", markup=markup, show=show_outcome_message
            )
            raise
        else:
            self.print(
                f"{message} {done_message}", markup=markup, show=show_outcome_message
            )
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

    #################################################################
    # Basic User Input/Output controls
    #################################################################

    def textwrap(self, text: str, width: int = MAX_TEXT_WIDTH) -> str:
        """Wrap text to the console width, a default max width, or a specified width."""
        # textwrap isn't really designed to format text that already contains newlines.
        # So, instead, break the text by newlines and format each line individually.
        return "\n".join(
            "\n".join(textwrap.wrap(line, width)) for line in text.splitlines()
        )

    def prompt(self, *values, markup=False, **kwargs):
        """Print to the screen for soliciting user interaction if input enabled.

        :param values: strings to print as the user prompt
        :param markup: True if prompt contains Rich markup
        """
        if self.input_enabled:
            self.print(*values, markup=markup, stack_offset=4, **kwargs)

    def divider(self, title: str = ""):
        """Writes a divider with an optional title.

        :param title: Optional; the title to display in the divider.
        """
        title = f"-- {title} " if title else ""
        self.prompt()
        self.prompt()
        self.prompt(f"{title}{'-' * (MAX_TEXT_WIDTH - len(title))}", style="bold")

    def input(self, prompt: str, *, markup: bool = False):
        """A simple input() interface, consistent with the Python builtin input().

        Prompt should be bold if markup is included.
        """
        if not self.input_enabled:
            raise InputDisabled()

        # make the prompt *bold* if it doesn't already contain markup
        escaped_prompt = f"[bold]{escape(prompt)}[/bold]" if not markup else prompt

        try:
            # Use underlying Rich input() to read from user
            input_value = self._console_impl.input(escaped_prompt, markup=True)
        except EOFError:
            raise KeyboardInterrupt

        self.to_log(prompt)
        self.to_log(f"User input: {input_value}")

        return input_value

    def input_boolean(self, question: str, default: bool = False) -> bool:
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
            yes_no = "[y/n]"
            default_text = None
        elif default:
            yes_no = "[Y/n]"
            default_text = "y"
        else:
            yes_no = "[y/N]"
            default_text = "n"

        prompt = f"{question} {yes_no}? "

        result = self.input_selection(
            prompt=prompt,
            choices=["y", "n"],
            default=default_text,
            error_message="Please enter Y or N",
            transform=lambda s: s.lower()[:1],
        )
        if result == "y":
            return True

        return False

    def input_selection(
        self,
        prompt: str,
        choices: Iterable[str],
        default: str | None = None,
        error_message: str = "Invalid Selection",
        transform: Callable[[str], str] | None = None,
    ) -> str:
        """Prompt the user to select an option from a list of choices.

        :param prompt: The text prompt to display
        :param choices: The list of available choices
        :param default: The default choice to select. If None,
        :param error_message: The error message to display to the user.
        :param transform: The text transform to apply to any user input before
            performing any validity checks.
        """
        while True:
            result = self.input_text(prompt, default)

            if transform is not None and result is not None:
                result = transform(result)

            if result in choices:
                return result

            self.warning()
            self.warning(error_message)
            self.warning()

    def input_text(self, prompt: str, default: str | None = None) -> str:
        """Prompt the user for text input.

        If no default is specified, the input will be returned as entered.

        The default will also be returned if input is disabled. If input is disabled,
        and there is no default, InputDisabled will be raised.

        :param prompt: The prompt to display to the user.
        :param default: (optional) The response to return if the user provides no input.
        :returns: The content entered by the user.
        """
        try:
            user_input = self.input(prompt)
            if default is not None and user_input == "":
                return default
        except InputDisabled:
            if default is not None:
                return default
            raise

        return user_input

    #################################################################
    # Advanced User Input/Output controls
    #################################################################

    def _validate(self, value, validator, usage="Invalid value") -> bool:
        """Validate a user-provided value.

        A warning message is printed if input is enabled. Otherwise, an exception is
        raised.

        :param value: The candidate value.
        :param validator: A validator function (or None, for no validation); accepts a
            single input (the candidate response), returns True if the value is valid,
            or raises ValueError() with a debugging message if the candidate value isn't
            valid.
        :raises InputDisabled: if console input has been disabled.
        :returns: True if the value is valid
        """
        try:
            if validator is None or validator(value):
                return True
            else:
                error_msg = repr(value)
        except ValueError as e:
            error_msg = str(e)

        if not self.input_enabled:
            raise InputDisabled(error_msg)

        self.prompt()
        self.prompt(f"{usage}: {error_msg}", style="bold yellow")

        return False

    def text_question(
        self,
        description,
        intro,
        default,
        validator=None,
        override_value=None,
    ) -> str:
        """Ask the user a question whose answer is text.

        :param description: A short description of the question being asked. This text
            is used in prompts and a header bar prefacing the question.
        :param intro: An introductory paragraph explaining the question being asked.
        :param default: The default value if the user hits enter without typing anything.
        :param validator: (optional) A validator function; accepts a single input (the
            candidate response), returns True if the answer is valid, or raises
            ValueError() with a debugging message if the candidate value isn't valid.
        :param override_value: A pre-selected answer for the question. This can be used
            to shortcut asking the question, such as when a command line option provides
            a value. If provided and valid, the header bar will be displayed, but the
            intro paragraph and option list will not.
        :returns: a string, guaranteed to meet the validation criteria of ``validator``
        """
        self.divider(title=description)

        if override_value is not None:
            self.print()
            self.print(f"Using override value {override_value!r}")
            if self._validate(
                override_value,
                validator,
                usage=f"Invalid override value for {description}",
            ):
                return override_value

        self.prompt()
        self.prompt(self.textwrap(intro))
        self.prompt()
        while True:
            answer = self.input_text(f"{description} [{default}]: ", default=default)

            if self._validate(answer, validator):
                return answer

            self.prompt()

    def selection_question(
        self,
        description: str,
        intro: str,
        options: Iterable[str] | Mapping[Any, str],
        default: str | None = None,
        override_value: str | None = None,
    ) -> Any:
        """Ask the user a question whose answer requires selecting from a list of
        options.

        The options are provided as a dictionary, or as a list of items. If a dictionary
        is provided, the values are the human-readable options, and the keys are the
        values that will be returned as the selection. The human-readable options will
        be sorted before display to the user. If a list is provided, the values in the
        list are both the user-displayed values and the returned value.

        :param description: A short description of the question being asked. This text
            is used in prompts and a header bar prefacing the question.
        :param intro: An introductory paragraph explaining the question being asked.
        :param options: The options to present to the user.
        :param default: The default option for empty user input. The options for the
            user start numbering at 1; so, to default to the first item, this should be
            "1".
        :param override_value: A pre-selected answer for the question. This can be used
            to shortcut asking the question, such as when a command line option provides
            a value. If provided and valid, the header bar will be displayed, but the
            intro paragraph and option list will not.
        :returns: The user's chosen option (the key of that option if options were
            provided as a dictionary)
        """
        self.divider(title=description)

        if override_value is not None:
            self.print()
            self.print(f"Using override value {override_value!r}")
            if self._validate(
                override_value,
                validator=lambda c: c in options,
                usage=f"Invalid override value for {description}",
            ):
                return override_value

        self.prompt()
        self.prompt(self.textwrap(intro))
        self.prompt()

        if isinstance(options, dict):
            ordered = list(options.items())
        else:
            ordered = list(zip(options, options, strict=True))

        if default is not None:
            try:
                default = str([option[0] for option in ordered].index(default) + 1)
            except ValueError:
                raise ValueError(f"{default!r} is not a valid default value")

        for i, (_, value) in enumerate(ordered, start=1):
            self.prompt(f"  {i}) {value}")

        self.prompt()

        choices = [str(index) for index in range(1, len(ordered) + 1)]
        index = self.input_selection(
            prompt=f"{description} [{default}]: " if default else f"{description}: ",
            choices=choices,
            error_message="Invalid Selection",
            default=default,
        )

        return ordered[int(index) - 1][0]

    def boolean_question(
        self,
        description,
        intro: str,
        default: bool | None = None,
        override_value: str | None = None,
    ) -> bool:
        """Ask the user a boolean question who's answer requires selecting yes/no.

        :param description: A short description of the question being asked. This text
            is used in prompts and a header bar prefacing the question.
        :param intro: An introductory paragraph explaining the question being asked.
        :param default: The default option for empty user input.
        :param override_value: A pre-selected answer for the question. This can be used
            to shortcut asking the question, such as when a command line option provides
            a value. If provided and valid, the header bar will be displayed, but the
            intro paragraph and option list will not. Will take the provided string and
            attempt to parse into bool
        :returns: The user's chosen answer or none if closed without input
        """

        self.divider(title=description)

        if override_value is not None:
            self.print()
            self.print(f"Using override value {override_value!r}")
            try:
                return parse_boolean(override_value)
            except ValueError as e:
                raise ValueError(f"Invalid override value for {description}: {e}")

        self.prompt()
        self.prompt(self.textwrap(intro))
        self.prompt()

        return self.input_boolean(description, default=default)
