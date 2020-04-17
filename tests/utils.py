from briefcase.console import Console, InputDisabled


class DummyConsole(Console):
    def __init__(self, *values, enabled=True):
        super().__init__(enabled=enabled)
        self.prompts = []
        self.values = list(values)

    def __call__(self, prompt):
        if not self.enabled:
            raise InputDisabled()
        self.prompts.append(prompt)
        return self.values.pop(0)
