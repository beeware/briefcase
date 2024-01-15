from unittest import mock

import pytest

from briefcase.commands.base import BaseCommand
from briefcase.console import Console, Log
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.app import macOSAppMixin, macOSCreateMixin
from tests.utils import DummyConsole


class DummyInstallCommand(macOSAppMixin, macOSCreateMixin, BaseCommand):
    """A dummy command to expose package installation capabilities."""

    command = "install"

    def __init__(self, base_path, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(base_path=base_path / "base_path", **kwargs)
        self.tools.input = DummyConsole()


@pytest.fixture
def dummy_command(tmp_path):
    cmd = DummyInstallCommand(base_path=tmp_path)

    cmd.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    return cmd
