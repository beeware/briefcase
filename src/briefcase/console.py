import contextlib
import operator
import os
import platform
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

from rich.console import Console as RichConsole
from rich.console import Group
from rich.highlighter import RegexHighlighter
from rich.live import Live
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


class InputDisabled(Exception):
    def __init__(self):
        super().__init__(
            "Input is disabled; cannot request user input without a default"
        )


class RichConsoleHighlighter(RegexHighlighter):
    """Custom Rich highlighter for printing to the console.

    This highlighter limits text highlighting to only URLs.

    By default, Rich applies several highlighting rules to anything it
    prints for concepts like UUIDs, markup, IP addresses, numbers, etc.
    All these colorful additions to the text can become overbearing and
    distracting given much of the output does not benefit from coloring.

    This defines a visually simpler style that highlights URLs in a way
    that is vaguely consistent with a default HTML stylesheet, but
    otherwise renders content as-is.
    """

    base_style = "repr."
    highlights = [r"(?P<url>(file|https|http|ws|wss)://[-0-9a-zA-Z$_+!`(),.?/;:&=%#]*)"]


class Printer:
    """Interface for printing and managing output to the console and/or log."""

    # Console to manage console output.
    console = RichConsole(
        highlighter=RichConsoleHighlighter(), emoji=False, soft_wrap=True
    )

    # Console to record all logging to a buffer while not printing anything to the console.
    # We need to be wide enough to render `sdkmanager --list_installed` output without
    # line wrapping.
    LOG_FILE_WIDTH = 180
    log = RichConsole(
        # Rich only records what's being logged if it is actually written somewhere;
        # writing to /dev/null allows Rich to do so without needing to print the logs
        # in the console or save them to file before it is known a file is wanted.
        file=open(os.devnull, "w", encoding="utf-8", errors="ignore"),
        record=True,
        width=LOG_FILE_WIDTH,
        no_color=True,
        markup=False,
        emoji=False,
        highlight=False,
        soft_wrap=True,
    )

    @classmethod
    def __call__(cls, *messages, stack_offset=5, show=True, **kwargs):
        """Entry point for all printing to the console and the log.

        The log records all content that is printed whether it is shown in
        the console or not (e.g. debug output). When execution completes,
        the log is conditionally exported and saved to a file.

        :param messages: content to print and/or log
        :param show: True (default) to print and log messages; False to only log.
        :param stack_offset: number of levels up the stack where logging was invoked.
            This tells Rich the number of levels to recurse up the stack to find
            the filename to put in the right column of the Rich log.
            Defaults to 5 since most uses are 5 levels deep from the actual logging.
        """
        if show:
            cls.to_console(*messages, **kwargs)
        cls.to_log(*messages, stack_offset=stack_offset, **kwargs)

    @classmethod
    def to_console(cls, *renderables, **kwargs):
        """Specialized print to the console only omitting the log."""
        cls.console.print(*renderables, **kwargs)

    @classmethod
    def to_log(cls, *renderables, stack_offset=5, **kwargs):
        """Specialized print to the log only omitting the console."""
        cls.log.log(*renderables, _stack_offset=stack_offset, **kwargs)

    @classmethod
    def export_log(cls):
        """Export the text of the entire log."""
        return cls.log.export_text()


class Log:
    """Manage logging output driven by verbosity flags."""

    # level of verbosity when debug output is shown in the console
    DEBUG = 2
    # printed at the beginning of all debug output
    DEBUG_PREFACE = ">>> "

    def __init__(self, printer=Printer(), verbosity=1):
        self.print = printer
        # verbosity will be 1 more than the number of v flags from invocation
        self.verbosity = verbosity
        # preserved Rich stacktrace of exception for logging to file
        self.stacktrace = None
        self.log_file_extras = []

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

        :param preface: value to be printed on the far left of the message and
            symbolic of the type of message being printed.
        :param prefix: text prepended to the message wrapped in brackets and will
            be presented as dimmer compared to the styling of the message text.
        :param message: text to log; can contain Rich tags if markup=True.
        :param show: True to print message to console; False to not print it.
            This is to allow logs to be saved to a file without printing them.
        :param markup: whether to interpret Rich markup in the prefix, preface,
            and message; if True, all text must already be escaped; defaults False.
        :param style: Rich style to apply to everything printed for message.
        """
        if not message:
            # When a message is not provided, do not output anything;
            # This type of call is just clearing some vertical space.
            self.print(show=show)
        else:
            if prefix:
                # insert vertical space before for all messages with a prefix
                self.print(show=show)
                if not markup:
                    preface, prefix, message = (
                        escape(text) for text in (preface, prefix, message)
                    )
                prefix = f"[dim]\\[{prefix}][/dim] "
                markup = True
            for line in message.splitlines():
                self.print(
                    f"{preface}{prefix}{line}",
                    show=show,
                    markup=markup,
                    style=style,
                )

    def debug(self, message="", *, prefix="", markup=False):
        """Log messages at debug level; included if verbosity>=2."""
        self._log(
            preface=self.DEBUG_PREFACE,
            prefix=prefix,
            message=message,
            show=self.verbosity >= self.DEBUG,
            markup=markup,
            style="dim",
        )

    def info(self, message="", *, prefix="", markup=False):
        """Log message at info level; always included in output."""
        self._log(prefix=prefix, message=message, markup=markup)

    def warning(self, message="", *, prefix="", markup=False):
        """Log message at warning level; always included in output."""
        self._log(prefix=prefix, message=message, markup=markup, style="bold yellow")

    def error(self, message="", *, prefix="", markup=False):
        """Log message at error level; always included in output."""
        self._log(prefix=prefix, message=message, markup=markup, style="bold red")

    def capture_stacktrace(self):
        """Preserve Rich stacktrace from exception while in except block."""
        self.stacktrace = Traceback.extract(*sys.exc_info(), show_locals=True)

    def add_log_file_extra(self, func):
        """Register a function to be called in the event that a log file is
        written.

        This can be used to provide additional debugging information
        which is too expensive to gather pre-emptively.
        """
        self.log_file_extras.append(func)

    def save_log_to_file(self, command):
        """Save the current application log to file."""
        # only save the log if a command ran and it errored or --log was specified
        if command is None or (not self.stacktrace and not command.save_log):
            return

        with command.input.wait_bar("Saving log...", transient=True):
            self.print.to_console()
            log_filename = f"briefcase.{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.{command.command}.log"
            log_filepath = command.base_path / log_filename
            try:
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
        if self.stacktrace:
            # using print.log.print() instead of print.to_log() to avoid
            # timestamp and code location inclusion for the stacktrace box.
            self.print.log.print(
                Traceback(
                    trace=self.stacktrace,
                    width=self.print.LOG_FILE_WIDTH,
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
                    except KeyboardInterrupt:
                        raise
                    except Exception:
                        self.error(traceback.format_exc())

        # build log header and export buffered log from Rich
        uname = platform.uname()
        sanitized_env_vars = "\n".join(
            f"    {env_var}={value if not SENSITIVE_SETTING_RE.search(env_var) else '********************'}"
            for env_var, value in sorted(command.os.environ.items())
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
    def __init__(self, printer=Printer(), enabled=True):
        self.print = printer
        self.input = printer.console.input
        self.enabled = enabled

        # Signal that Rich is dynamically controlling the console output.
        # Therefore, all output must be printed to the console by Rich to
        # prevent corruption by dynamic elements like the Wait Bar.
        self.is_output_controlled = False

        self._live_display: Live = None
        self._live_display_stack = []
        self._wait_bar: Progress = None

    def _live_display_add(self, renderable):
        """Add a renderable to the top of the Live Display."""
        if renderable not in self._live_display_stack:
            self._live_display_stack.append(renderable)
            self._live_display_update()

    def _live_display_remove(self, renderable):
        """Remove a renderable from the Live Display."""
        with contextlib.suppress(ValueError):
            self._live_display_stack.remove(renderable)
        self._live_display_update()
        # Print non-transient renderables so their final refresh remains in
        # the console. When a renderable is removed from the Live Display,
        # it is also completely removed from the console.
        if not renderable.live.transient:
            self.print(renderable)

    def _live_display_update(self):
        """Update the Live Display with the current stack of renderables."""
        if not self._live_display:
            self._live_display = Live(
                refresh_per_second=15,
                transient=True,
                console=self.print.console,
            )
        if self._live_display_stack:
            self.is_output_controlled = True
            self._live_display.update(
                Group(*self._live_display_stack[::-1]),
                refresh=True,
            )
            self._live_display.start()
        else:
            self._live_display.stop()
            self.is_output_controlled = False

    def remove_dynamic_elements(self):
        """Remove dynamic console elements such as the Wait bar.

        Only remove with the intent to restore. Otherwise, when the
        context managers for the currently active elements exit, screen
        corruption may occur.
        """
        if self._live_display:
            self._live_display.stop()
            # Force creation of new Live Display when it is restored.
            # This ensures the Live Display doesn't corrupt console
            # content created after the existing one was stopped.
            self._live_display = None
            self.is_output_controlled = False

    def restore_dynamic_elements(self):
        """Restore previously removed dynamic console elements."""
        self._live_display_update()

    @contextlib.contextmanager
    def progress_bar(self):
        """Returns a progress bar as a context manager."""
        progress_bar = Progress(
            TextColumn("  "),
            SpinnerColumn("line", speed=1.5, style="default"),
            BarColumn(bar_width=50),
            TextColumn("{task.percentage:>3.1f}%", style="default"),
            TextColumn("•", style="default"),
            TimeRemainingColumn(compact=True, elapsed_when_finished=True),
            console=self.print.console,
        )
        try:
            self._live_display_add(progress_bar)
            yield progress_bar
        finally:
            self._live_display_remove(progress_bar)

    @contextlib.contextmanager
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
                console=self.print.console,
            )
            # start=False causes the progress bar to "pulse"
            # message=None is a sentinel the Wait Bar should be inactive
            self._wait_bar.add_task("", start=False, message=None)

        wait_bar_task = self._wait_bar.tasks[0]
        previous_message = wait_bar_task.fields["message"]
        self._wait_bar.update(wait_bar_task.id, message=message)
        self._live_display_add(self._wait_bar)
        try:
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
                self._live_display_remove(self._wait_bar)

    def boolean_input(self, question, default=False):
        """Get a boolean input from user, in the form of y/n.

        The user might press "y" for true or "n" for false.
        If input is disabled, returns default. If input is disabled and default
        is *not* defined, InputDisabled is raised.

        :param question: A string message specifying the question to be
            answered by the user.
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

        The default will also be returned if input is disabled. If input is
        disabled, and there is no default, InputDisabled will be raised.

        :param prompt: The prompt to display to the user.
        :param default: (optional) The response to return if the user provides
            no input.
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

    def prompt(self, *values, markup=False, **kwargs):
        """Print to the screen for soliciting user interaction.

        :param values: strings to print as the user prompt
        :param markup: True if prompt contains Rich markup
        """
        if self.enabled:
            self.print(*values, markup=markup, stack_offset=4, **kwargs)

    def __call__(self, prompt, *, markup=False):
        """Present input() interface."""
        if not self.enabled:
            raise InputDisabled()
        try:
            input_value = self.input(prompt, markup=markup)
            self.print.to_log(prompt)
            self.print.to_log(f"{Log.DEBUG_PREFACE}User input: {input_value}")
            return input_value
        except EOFError:
            raise KeyboardInterrupt


def select_option(options, input, prompt="> ", error="Invalid selection"):
    """Prompt the user for a choice from a list of options.

    The options are provided as a dictionary; the values are the
    human-readable options, and the keys are the values that will
    be returned as the selection. The human-readable options
    will be sorted before display to the user.

    This method does *not* print a question or any leading text;
    it only prints the list of options, and prompts the user
    for their choice. If the user chooses an invalid selection (either
    provides non-integer input, or an invalid integer), it prints an
    error message and prompts the user again.

    :param options: A dictionary, or list of tuples, of options to present to
        the user.
    :param input: The function to use to retrieve the user's input. This
        exists so that the user's input can be easily mocked during testing.
    :param prompt: The prompt to display to the user.
    :param error: The error message to display when the user provides invalid
        input.
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
    index = input.selection_input(prompt=prompt, choices=choices, error_message=error)
    return ordered[int(index) - 1][0]
