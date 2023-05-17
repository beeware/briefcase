from unittest.mock import MagicMock

import pytest

from briefcase.platforms.linux import LinuxMixin


@pytest.fixture
def linux_mixin():
    """A Linux mixin with a mocked tools collection."""
    linux_mixin = LinuxMixin()
    linux_mixin.tools = MagicMock()
    return linux_mixin
