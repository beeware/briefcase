import operator


def select_option(options, input=input, prompt='> ', error="Invalid selection"):
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
    while True:
        try:
            selection = int(input(prompt))
            return ordered[selection - 1][0]
        except (ValueError, IndexError):
            print(error)
