import os
import re
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.virtual_environment import VenvContext



"""Tests for the VenvContext.create method."""

def test_create(self, dummy_tools, venv_path):
    """Tests create creates a venv at the specified path."""
    context = VenvContext(dummy_tools, venv_path)

    # Mock the methods that create() calls
    context.update_core_tools = MagicMock()
    dummy_tools.subprocess.run = MagicMock()

    # Call create
    context.create()

    # Verify subprocess.run was called with correct arguments
    dummy_tools.subprocess.run.assert_called_once_with(
        [sys.executable, "-m", "venv", os.fspath(venv_path)],
        check=True,
    )

    # Verify update_core_tools was called
    context.update_core_tools.assert_called_once()

def test_create_subprocess_fails(self, dummy_tools, venv_path):
    """Tests create raises BriefcaseCommandError if subprocess fails."""
    context = VenvContext(dummy_tools, venv_path)

    context.update_core_tools = MagicMock()

    dummy_tools.subprocess.run = MagicMock(
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

    dummy_tools.subprocess.run.assert_called_once_with(
        [sys.executable, "-m", "venv", os.fspath(venv_path)],
        check=True,
    )

    context.update_core_tools.assert_not_called()
