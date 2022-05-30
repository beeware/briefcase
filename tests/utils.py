from unittest.mock import MagicMock

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


# Consider to remove  class definition when we drop python 3.7 support.
class FsPathMock(MagicMock):
    def __init__(self, path):
        super().__init__()
        self.path = path

    def __fspath__(self):
        return self.path

    def _get_child_mock(self, **kw):
        """Create child mocks with right MagicMock class."""
        return MagicMock(**kw)
