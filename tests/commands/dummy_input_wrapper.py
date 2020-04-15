from collections import deque
from briefcase.console import InputWrapper


class DummyInputWrapper(InputWrapper):

    def __init__(self, *values, enabled=True):
        super(DummyInputWrapper, self).__init__(enabled=enabled)
        self.prompts = []
        self.values = deque()
        self.set_values(*values)

    def set_values(self, *values):
        self.values.extend(values)

    def __call__(self, prompt):
        self.prompts.append(prompt)
        return self.values.popleft()
