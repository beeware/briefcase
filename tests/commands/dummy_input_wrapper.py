from briefcase.input_wrapper import InputWrapper


class DummyInputWrapper(InputWrapper):

    def __init__(self, enabled=True):
        super(DummyInputWrapper, self).__init__(enabled=enabled)
        self.prompts = []
        self.value = None

    def set_value(self, value):
        self.value = value

    def __call__(self, prompt):
        self.prompts.append(prompt)
        return self.value
