import re
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.virtual_environment import VenvContext


def test_create(mock_tools, venv_path):
    """Tests create creates a venv at the specified path."""
    context = VenvContext(mock_tools, venv_path)

    # Mock the methods that create() calls
    context.update_core_tools = MagicMock()
    mock_tools.subprocess.run = MagicMock()

    # Call create
    context.create()

    # Verify subprocess.run was called with correct arguments
    mock_tools.subprocess.run.assert_called_once_with(
        [sys.executable, "-m", "venv", venv_path],
        check=True,
    )

    # Verify update_core_tools was called
    context.update_core_tools.assert_called_once()


def test_create_subprocess_fails(mock_tools, venv_path):
    """Tests create raises BriefcaseCommandError if subprocess fails."""
    context = VenvContext(mock_tools, venv_path)

    context.update_core_tools = MagicMock()

    mock_tools.subprocess.run = MagicMock(
        side_effect=subprocess.CalledProcessError(returncode=1, cmd="venv")
    )

    escaped_venv_path = re.escape(
        str(venv_path)
    )  # Escape backslashes for regex match, windows backslashes

    with pytest.raises(
        BriefcaseCommandError,
        match=f"Failed to create virtual environment at {escaped_venv_path}",
    ):
        context.create()

    mock_tools.subprocess.run.assert_called_once_with(
        [sys.executable, "-m", "venv", venv_path],
        check=True,
    )

    context.update_core_tools.assert_not_called()
