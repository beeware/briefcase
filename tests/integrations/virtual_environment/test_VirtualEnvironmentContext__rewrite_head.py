import sys
from pathlib import Path

import pytest

from briefcase.integrations.virtual_environment import VenvContext



"""Test cases for the VenvContext.rewrite_head method."""

@pytest.mark.parametrize(
    "empty_args",
    [
        [],
        (),
        None,
    ],
)
def test_rewrite_head_empty(self, venv_context: VenvContext, empty_args):
    """Test that rewrite_head returns empty inputs unchanged."""
    result = venv_context._rewrite_head(empty_args)
    assert result == empty_args

@pytest.mark.parametrize(
    "args, expected_suffix",
    [
        ([sys.executable], []),
        (
            [sys.executable, "-m", "pip", "install", "package"],
            ["-m", "pip", "install", "package"],
        ),
        ([Path(sys.executable), "-c", "print('hello')"], ["-c", "print('hello')"]),
    ],
)
def test_rewrite_head_system_python_replacement(
    self, venv_context: VenvContext, args, expected_suffix
):
    """Test _rewrite_head replaces sys.executable with venv executable."""
    result = venv_context._rewrite_head(args)

    expected = [venv_context.executable] + expected_suffix
    assert result == expected

@pytest.mark.parametrize(
    "args",
    [
        ["/usr/bin/python3"],
        ["pip", "install", "package"],
        ("python", "-c", "import sys"),
    ],
)
def test_rewrite_head_no_replacement(self, venv_context: VenvContext, args):
    """Test _rewrite_head preserves non-matching commands and converts to list."""
    result = venv_context._rewrite_head(args)
    expected = list(args)
    assert result == expected
    assert isinstance(result, list)

@pytest.mark.skipif(
    sys.platform == "win32", reason="Unix specific case handling test"
)
def test_rewrite_head_case_insensitive_match(self, venv_context):
    """Test _rewrite_head handles case-insensitive matching via normcase."""
    case_variant = sys.executable

    args = [case_variant, "-V"]
    result = venv_context._rewrite_head(args)

    expected = [venv_context.executable, "-V"]
    assert result == expected

@pytest.mark.skipif(
    sys.platform != "win32", reason="Windows specific case handling test"
)
def test_rewrite_head_case_insensitive_match_nt(self, venv_context):
    case_variant = (
        sys.executable.upper()
        if sys.executable.islower()
        else sys.executable.lower()
    )
    args = [case_variant, "-V"]
    result = venv_context._rewrite_head(args)

    expected = [venv_context.executable, "-V"]
    assert result == expected
