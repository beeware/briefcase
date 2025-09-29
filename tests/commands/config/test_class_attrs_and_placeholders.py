import io

import pytest

from briefcase.commands.config import ConfigCommand


class DummyConsole:
    def __init__(self):
        self.buf = io.StringIO()

    def print(self, *a, **k):
        self.buf.write(" ".join(map(str, a)) + "\n")


def test_class_attributes_are_defined():
    cmd = ConfigCommand(console=DummyConsole())
    assert cmd.command == "config"
    assert isinstance(cmd.description, str) and cmd.description


def test_placeholder_methods_raise_not_implemented():
    cmd = ConfigCommand(console=DummyConsole())
    with pytest.raises(NotImplementedError):
        cmd.bundle_path(None)
    with pytest.raises(NotImplementedError):
        cmd.binary_path(None)
    with pytest.raises(NotImplementedError):
        cmd.distribution_path(None)
    with pytest.raises(NotImplementedError):
        cmd.binary_executable_path(None)
