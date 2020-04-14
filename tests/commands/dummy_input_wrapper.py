from collections import deque
from briefcase.input_wrapper import InputWrapper


class DummyInputWrapper(InputWrapper):

    def __init__(self, enabled=True):
        super(DummyInputWrapper, self).__init__(enabled=enabled)
        self.prompts = []
        self.values = deque()

    def set_values(self, *values):
        self.values.extend(values)

    def __call__(self, prompt):
        self.prompts.append(prompt)
        return self.values.popleft()
