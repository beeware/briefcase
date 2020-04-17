import operator


class InputDisabled(Exception):
    def __init__(self):
        super().__init__(
            "Input is disabled; cannot request user input without a default"
        )


class Console:
    def __init__(self, enabled=True):
        self._enabled = enabled
        self._input = input

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled

    def boolean_input(self, question, default=False):
        """
        Get a boolean input from user, in the form of y/n.

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
            default_text = 'y'
        else:
            yes_no = "[y/N]"
            default_text = 'n'

        prompt = "{question} {yes_no}? ".format(question=question, yes_no=yes_no)

        result = self.selection_input(
            prompt=prompt,
            choices=['y', 'n'],
            default=default_text,
            error_message="Please enter Y or N",
            transform=lambda s: s.lower()[:1],
        )
        if result == 'y':
            return True

        return False

    def selection_input(
        self,
        prompt,
        choices,
        default=None,
        error_message="Invalid Selection",
        transform=None
    ):
        """
        Prompt the user to select an option from a list of choices.

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

            print()
            print(error_message)

    def text_input(self, prompt, default=None):
        """
        Prompt the user for text input.

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

    def __call__(self, prompt):
        "Make Console present the same interface as input()"
        if not self.enabled:
            raise InputDisabled()

        return self._input(prompt)


def select_option(options, input, prompt='> ', error="Invalid selection"):
    """
    Prompt the user for a choice from a list of options.

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
        ordered = list(
            sorted(
                options.items(),
                key=operator.itemgetter(1)
            )
        )
    else:
        ordered = options

    if input.enabled:
        for i, (key, value) in enumerate(ordered, start=1):
            print('  {i}) {label}'.format(i=i, label=value))

        print()

    choices = [str(index) for index in range(1, len(ordered) + 1)]
    index = input.selection_input(prompt=prompt, choices=choices, error_message=error)
    return ordered[int(index) - 1][0]
