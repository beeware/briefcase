from unittest.mock import Mock, patch

import pytest

from briefcase.integrations.virtual_environment import VenvContext



"""Test cases for VenvContext.check_output method."""

@pytest.mark.parametrize(
    "env_override, other_kwargs",
    [
        (None, {}),
        ({"CUSTOM": "value"}, {}),
        (None, {"cwd": "/tmp", "timeout": 30}),
        ({"PATH": "/custom"}, {"cwd": "/tmp", "shell": True}),
    ],
)
def test_check_output_environment_handling(
    self, venv_context: VenvContext, env_override, other_kwargs
):
    """Test check_output properly handles environment and kwargs."""

    mock_rewrite_head = Mock(return_value=["rewritten", "args"])
    mock_full_env = Mock(return_value={"FULL": "env"})
    mock_subprocess = Mock()
    mock_subprocess.check_output.return_value = "output"

    kwargs = other_kwargs.copy()
    if env_override is not None:
        kwargs["env"] = env_override

    with (
        patch.object(venv_context, "_rewrite_head", mock_rewrite_head),
        patch.object(venv_context, "full_env", mock_full_env),
        patch.object(venv_context.tools, "subprocess", mock_subprocess),
    ):
        result = venv_context.check_output(["test"], **kwargs)

        mock_full_env.assert_called_once_with(env_override)

        expected_kwargs = other_kwargs.copy()
        expected_kwargs["env"] = {"FULL": "env"}

        mock_subprocess.check_output.assert_called_once_with(
            ["rewritten", "args"], **expected_kwargs
        )

        assert result == "output"

def test_check_output_kwargs_env_extraction(self, venv_context: VenvContext):
    """Test check_output properly extracts env from kwargs."""
    mock_rewrite_head = Mock(return_value=["args"])
    mock_full_env = Mock(return_value={"MERGED": "env"})
    mock_subprocess = Mock()
    mock_subprocess.check_output.return_value = "output"

    original_kwargs = {
        "env": {"CUSTOM": "value"},
        "cwd": "/tmp",
        "timeout": 30,
        "shell": False,
    }
    kwargs_copy = original_kwargs.copy()

    with (
        patch.object(venv_context, "_rewrite_head", mock_rewrite_head),
        patch.object(venv_context, "full_env", mock_full_env),
        patch.object(venv_context.tools, "subprocess", mock_subprocess),
    ):
        venv_context.check_output(["test"], **original_kwargs)

        assert original_kwargs == kwargs_copy

        mock_full_env.assert_called_once_with({"CUSTOM": "value"})

        expected_call_kwargs = {
            "cwd": "/tmp",
            "timeout": 30,
            "shell": False,
            "env": {"MERGED": "env"},
        }
        mock_subprocess.check_output.assert_called_once_with(
            ["args"], **expected_call_kwargs
        )
