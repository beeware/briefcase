

class InputWrapper:
    YES = "y"
    NO = "n"

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
        default_text = self.YES if default else self.NO
        result = self.text_input(
            "{question} {yes_no}".format(question=question, yes_no=yes_no),
            default=default_text
        )
        if result.lower() == self.YES:
            return True
        if result.lower() == self.NO:
            return False
        return default

    def selection_input(
            self,
            prompt,
            choices,
            default,
            error_message="Invalid Selection"
    ):
        while True:
            result = self.text_input(prompt, default)

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
        return input(prompt)
