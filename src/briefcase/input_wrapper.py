class InputWrapper:

    def __init__(self, enabled=True):
        self.enabled = enabled

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def __call__(self, prompt):
        return input(prompt)
