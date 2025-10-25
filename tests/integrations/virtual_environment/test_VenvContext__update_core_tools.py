import re
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.virtual_environment import VenvContext


def test_update_core_tools_success(mock_tools, venv_path):
    """update_core_tools succeeds."""
    context = VenvContext(mock_tools, venv_path)
    context.run = MagicMock()
    context.update_core_tools()
    context.run.assert_called_once_with(
        [context.executable, "-m", "pip", "install", "-U", "pip"],
        check=True,
    )


def test_update_core_tools_failure(mock_tools, venv_path):
    """Update core tools raise BriefcaseCommandError if subprocess fails."""
    context = VenvContext(mock_tools, venv_path)
    test_exception = RuntimeError("pip install failed")
    context.run = MagicMock(side_effect=test_exception)
    escaped_venv_path = re.escape(
        str(venv_path)
    )  # Escape backslashes for regex match, windows backslashes
    with pytest.raises(
        BriefcaseCommandError,
        match=f"Failed to update core tooling for {escaped_venv_path}",
    ):
        context.update_core_tools()
    context.run.assert_called_once_with(
        [context.executable, "-m", "pip", "install", "-U", "pip"],
        check=True,
    )
