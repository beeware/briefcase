import contextlib
import operator

from rich.console import Console as RichConsole
from rich.highlighter import RegexHighlighter
from rich.markup import escape
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)


class InputDisabled(Exception):
    def __init__(self):
        super().__init__(
            "Input is disabled; cannot request user input without a default"
        )


class RichConsoleHighlighter(RegexHighlighter):
    """Custom Rich highlighter for printing to the terminal.

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


rich_console = RichConsole(highlighter=RichConsoleHighlighter(), emoji=False)


class Log:
    """Manage logging output driven by verbosity flags."""

    DEBUG = 2
    DEEP_DEBUG = 3

    def __init__(self, verbosity=1):
        self.rich_console = rich_console
        # verbosity will be 1 more than the number of v flags from invocation
        self.verbosity = verbosity
        # value to be printed at the beginning of all debug output
        self.debug_preface = ">>> "

    def _log(self, preface="", prefix="", message="", markup=False, style=None):
        """Funnel to log all messages.

        :param preface: value to be printed on the far left of the message and
            symbolic of the type of message being printed.
        :param prefix: text prepended to the message wrapped in brackets and will
            be presented as dimmer compared to the styling of the message text.
        :param message: text to log; can contain Rich tags if markup=True.
        :param markup: whether to interpret Rich markup in the prefix, preface,
            and message; if True, all text must already be escaped; defaults False.
        :param style: Rich style to apply to everything printed for message.
        """
        if not message:
            # When a message is not provided, do not output anything;
            # This type of call is just clearing some vertical space.
            self.rich_console.print()
        else:
            if prefix:
                if not markup:
                    preface, prefix, message = (
                        escape(text) for text in (preface, prefix, message)
                    )
                prefix = f"[dim]\\[{prefix}][/dim] "
                markup = True
            for line in message.splitlines():
                self.rich_console.print(
                    f"{preface}{prefix}{line}", markup=markup, style=style
                )

    def deep_debug(self, message="", *, prefix="", markup=False):
        """Log messages at deep debug level; included if verbosity>=3."""
        if self.verbosity >= self.DEEP_DEBUG:
            self._log(
                preface=self.debug_preface,
                prefix=prefix,
                message=message,
                markup=markup,
                style="dim",
            )

    def debug(self, message="", *, prefix="", markup=False):
        """Log messages at debug level; included if verbosity>=2."""
        if self.verbosity >= self.DEBUG:
            self._log(
                preface=self.debug_preface,
                prefix=prefix,
                message=message,
                markup=markup,
                style="dim",
            )

    def info(self, message="", *, prefix="", markup=False):
        """Log message at info level; always included in output."""
        self._log(prefix=prefix, message=message, markup=markup)

    def warning(self, message="", *, prefix="", markup=False):
        """Log message at warning level; always included in output."""
        self._log(prefix=prefix, message=message, markup=markup)

    def error(self, message="", *, prefix="", markup=False):
        """Log message at error level; always included in output."""
        self._log(prefix=prefix, message=message, markup=markup)


class Console:
    def __init__(self, enabled=True):
        self.rich_console = rich_console
        self._enabled = enabled

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled

    def prompt(self, *values, markup=False, **kwargs):
        """Print to the screen for soliciting user interaction.

        :param values: strings to print as the user prompt
        :param markup: True if prompt contains Rich markup
        """
        if self.enabled:
            self.rich_console.print(*values, markup=markup, **kwargs)

    def progress_bar(self):
        """Returns a progress bar as a context manager."""
        return Progress(
            TextColumn("  "),
            SpinnerColumn("line", speed=1.5, style="default"),
            BarColumn(bar_width=50),
            TextColumn("{task.percentage:>3.1f}%", style="default"),
            TextColumn("•", style="default"),
            TimeRemainingColumn(compact=True, elapsed_when_finished=True),
            console=self.rich_console,
        )

    @contextlib.contextmanager
    def wait_bar(
        self, message="", done_message="done", *, transient=False, markup=False
    ):
        """Returns a wait bar as a context manager.

        :param message: text explaining what is being awaited
        :param done_message: text appended to the message after exiting
        :param transient: if True, remove bar and message from screen after exiting;
            if False (default), the message will remain on the screen without pulsing bar.
        :param markup: whether to interpret Rich styling markup in the message; if True,
            the message must already be escaped; defaults False.
        """
        wait_bar = Progress(
            TextColumn("     "),
            BarColumn(bar_width=40, style="black", pulse_style="white"),
            TextColumn(message),
            transient=True,
            console=self.rich_console,
        )
        # setting start=False causes the progress bar to pulse
        wait_bar.add_task("", start=False)
        try:
            with wait_bar:
                yield
        except BaseException:
            # ensure the message is left on the screen even if user sends CTRL+C
            if message and not transient:
                self.rich_console.print(message, markup=markup)
            raise
        else:
            if message and not transient:
                self.rich_console.print(
                    f'{message}{f" {done_message}" if done_message else ""}',
                    markup=markup,
                )

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

    def __call__(self, prompt, *, markup=False):
        """Make Console present the same interface as input()"""
        if not self.enabled:
            raise InputDisabled()
        try:
            return self.rich_console.input(prompt, markup=markup)
        except EOFError:
            raise KeyboardInterrupt


def select_option(options, input, prompt="> ", error="Invalid selection"):
    """Prompt the user for a choice from a list of options.

    The options are provided as a dictionary; the values are the
    human-readable options, and the keys are the values that will
    be returned as the selection. The human readable options
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
