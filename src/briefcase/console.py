import operator


class InputWrapperDisabledError(Exception):
    def __init__(self):
        super(InputWrapperDisabledError, self).__init__(
            "Cannot call input __call__ method when it is disabled"
        )


class InputWrapper:
    YES_DEFAULT = "y"
    NO_DEFAULT = "n"
    YES_OPTIONS = ["y", "yes"]
    NO_OPTIONS = ["n", "no"]
    ALL_OPTIONS = YES_OPTIONS + NO_OPTIONS

    def __init__(self, enabled=True):
        self.__enabled = enabled

    @property
    def enabled(self):
        return self.__enabled

    @enabled.setter
    def enabled(self, enabled):
        self.__enabled = enabled

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def boolean_input(self, question, default=False):
        """
        Get a boolean input from user.
        The user might press "y" for true or "n" for false.
        If input is disabled, returns default.

        :param question:
            a string message specifying the question to be answered by the user.
        :param default:
            default answer
        :return:
            True or False, based on user input or default value
        """
        yes_no = "[Y,n]" if default else "[y,N]"
        default_text = self.YES_DEFAULT if default else self.NO_DEFAULT
        prompt = "{question} {yes_no}: ".format(question=question, yes_no=yes_no)
        error_message = (
            "Invalid Input; please enter one of the followings: "
            f"{', '.join(self.ALL_OPTIONS)}"
        )
        result = self.selection_input(
            prompt=prompt,
            choices=self.ALL_OPTIONS,
            default=default_text,
            error_message=error_message,
            transform=str.lower
        )
        if result.lower() in self.YES_OPTIONS:
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
        while True:
            result = self.text_input(prompt, default)

            if transform is not None:
                result = transform(result)

            if result in choices:
                return result

            print()
            print(error_message)

    def text_input(self, prompt, default):
        if not self.enabled:
            return default
        user_input = self(prompt)
        if user_input == "":
            return default
        return user_input

    def __call__(self, prompt):
        if not self.enabled:
            raise InputWrapperDisabledError()
        return self._actual_input(prompt)

    def _actual_input(self, prompt):
        return input(prompt)


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

    :param options: A dictionary of options to present to the user.
    :param input: The function to use to retrieve the user's input. This
        exists so that the user's input can be easily mocked during testing.
    :param prompt: The prompt to display to the user.
    :param error: The error message to display when the user provides invalid
        input.
    :returns: The key corresponding to the user's chosen option.
    """
    ordered = list(
        sorted(
            options.items(),
            key=operator.itemgetter(1)
        )
    )

    for i, (key, value) in enumerate(ordered, start=1):
        print('  {i}) {label}'.format(i=i, label=value))

    print()
    choices = [str(index) for index in range(1, len(ordered) + 1)]
    index = input.selection_input(prompt=prompt, choices=choices, error_message=error)
    return ordered[int(index) - 1][0]
