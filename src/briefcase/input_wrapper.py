class InputWrapper:

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
        if not self.enabled:
            return default
        yes_no = "[Y,n]" if default else "[y,N]"
        result = self("{question} {yes_no}".format(question=question, yes_no=yes_no))
        if result.lower() == "y":
            return True
        if result.lower() == "n":
            return False
        return default

    def __call__(self, prompt):
        return input(prompt)
