import operator
from functools import partial

from .exceptions import BriefcaseCommandError


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

    @staticmethod
    def titlecase(s):
        """
        Convert a string to titlecase.

        Follow Chicago Manual of Style rules for capitalization (roughly).

        * Capitalize *only* the first letter of each word
        * ... unless the word is an acronym (e.g., URL)
        * ... or the word is on the exclude list ('of', 'and', 'the)
        :param s: The input string
        :returns: A capitalized string.
        """
        return ' '.join(
            word if (
                    word.isupper()
                    or word in {
                        'a', 'an', 'and', 'as', 'at', 'but', 'by', 'en', 'for',
                        'if', 'in', 'of', 'on', 'or', 'the', 'to', 'via', 'vs'
                    }
            ) else word.capitalize()
            for word in s.split(' ')
        )

    def print(self, *values, **kwargs):
        """
        Wrapper for all printing to the screen for the intention of soliciting
        user interaction or displaying ephemeral information such as file
        download status or simulator startup status.
        """
        if self.enabled:
            print(*values, **kwargs)

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

        def normalize_input(user_input):
            """Normalize user input to just the lowercase version of the first character."""
            return user_input.lower()[:1]

        def is_y_or_n(user_input):
            """Validator for text_input() that user entered a literal 'y' or 'n'."""
            if normalize_input(user_input) in {'y', 'n'}:
                return True
            raise ValueError("Please enter Y or N")

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
        result = self.text_input(prompt=prompt, default=default_text, validator=is_y_or_n)

        # return True for yes, False for no
        return normalize_input(result) == 'y'

    def selection_input(self, intro=None, prompt="", options=None, input_name=None, default=None):
        """
        Prompt the user to select an option from a list of choices.

        If intro is specified, it will be presented once prior to the input prompt.
        The behavior of prompt is deferred to text_input().

        The list of options can be a dictionary, list of 2 item lists, or a literal list:
            Dictionary
                If provided as a dictionary, the values are the
                human-readable options, and the keys are the values that will
                be returned as the selection. The human-readable options
                will be sorted before display to the user.
            List of 2 item lists
                If provided as a list of lists, the second item in the inner lists
                are the human-readable options. The first item will be returned as
                the selection.
            List of strings
                If provided as a simple list of choices, those choices will be
                used as the human-readable options and returned as the selection.

        Default Value
            For dictionary options, the default should be a dictionary key.
            For list of lists, the default should be the first item in one of the inner lists.
            For a simple list, the default should be a value in the list.

        :param intro: An introductory paragraph explaining the question being asked.
        :param prompt: The text prompt to display after the choices are printed.
            See text_input for prompt defaulting.
        :param options: The list of available choices.
        :param input_name: (optional) logical name of the value being requested; only
            used as part of prompt for the user if a value for prompt is not provided.
        :param default: The default choice to select. Must be dictionary key or value in list.
        """

        def is_valid_choice(user_input: str, choices: set):
            """Validator for text_input() for a specific range of integers."""
            if user_input in choices:
                return True
            raise ValueError("Enter a number from {start} to {end}".format(start=min(choices), end=max(choices)))

        if intro:
            self.print(intro)
            self.print()

        # normalize the options in to a list of 2-item tuples
        if isinstance(options, dict):
            ordered = list(
                sorted(
                    options.items(),
                    key=operator.itemgetter(1)
                )
            )
        elif all(isinstance(item, (tuple, list)) for item in options):
            ordered = options
        else:
            ordered = [(item, item) for item in options]

        # display the options to the user
        adjusted_default = None
        for i, (key, value) in enumerate(ordered, start=1):
            self.print('  {i}) {label}'.format(i=i, label=value))
            # recalculate the default for text_input
            if default is not None and key == default:
                adjusted_default = str(i)
        # ensure a default is not passed to text_input unless it was actually found in the options
        default = adjusted_default
        self.print()

        # while the internal value of the choices being considered are integers, making them
        # strings avoids corner cases where strings could be confusingly coerced to integers
        # for purposes of validation. For instance, if "9.0" is provided to text_input, then
        # technically int("9.0") (which returns 9) would be considered valid for >=9 choices.
        validator = partial(is_valid_choice, choices=set(map(str, range(1, len(ordered)+1))))
        choice = self.text_input(prompt=prompt, input_name=input_name, default=default, validator=validator)
        return ordered[int(choice) - 1][0]

    def text_input(self, intro=None, prompt="", input_name=None, default=None, validator=None):
        """
        Prompt the user for text input.

        If intro is specified, it will be presented once prior to the input prompt.

        If prompt is not specified, a prompt of the form "{input_name} [{default}}: "
            will be shown to the user.
        If prompt is specified, it is shown to the user and input_name is ignored.

        If validator is not specified:
            the user's input is returned.
            If the user enters nothing, the default value is returned if specified,
                else an empty string is returned.

        If validator is specified:
            the reason for invalidation will be shown to the user.
            input will be continuously requested until validation succeeds.

        if input is disabled:
            Neither intro nor prompt will be printed.
            The default will be returned.
            If default is not specified, InputDisabled will be raised.

        :param intro: An introductory paragraph explaining the question being asked.
        :param prompt: The prompt to display to the user; if omitted, the prompt
            "{input_name} [{default}}: " will be presented to the user.
        :param input_name: (optional) logical name of the value being requested; only
            used as part of prompt for the user if a value for prompt is not provided.
        :param default: (optional) The response to return if the user provides
            no input. Will be coerced to a string.
        :param validator: (optional) A validator function; accepts a single
            input (the candidate response), returns True if the answer is
            valid, or raises ValueError() with a debugging message if the
            candidate value isn't valid.
        :returns: string of the content entered by the user.
        """
        if intro:
            self.print(intro)
            self.print()

        if self.enabled and not prompt and input_name:
            prompt = self.titlecase(input_name)
            prompt += " [{default}]".format(default=default) if default is not None else ""
            prompt += ": "

        while True:
            try:
                user_input = self(prompt)
                if default is not None and user_input == "":
                    user_input = default
            except InputDisabled:
                if default is None:
                    raise
                user_input = default

            if validator is not None:
                try:
                    validator(user_input)
                except ValueError as e:
                    if not self.enabled:
                        raise BriefcaseCommandError(str(e))

                    self.print()
                    self.print("Invalid value; {e}".format(e=e))
                    self.print()
                    continue

            return str(user_input)

    def __call__(self, prompt):
        "Make Console present the same interface as input()"
        if not self.enabled:
            raise InputDisabled()
        try:
            return self._input(prompt)
        except EOFError:
            raise KeyboardInterrupt
