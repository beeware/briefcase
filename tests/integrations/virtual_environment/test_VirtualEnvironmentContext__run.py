import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from briefcase.integrations.virtual_environment import VenvContext


class TestRun:
    """Test cases for VenvContext.run method."""

    @pytest.mark.parametrize(
        "args, expected_rewritten_args",
        [
            ([sys.executable, "-V"], "VENV_PYTHON_WITH_ARGS"),
            (["pip", "list"], ["pip", "list"]),
            ((sys.executable, "-c", "print('test')"), "VENV_PYTHON_WITH_ARGS"),
            ([Path(sys.executable)], "VENV_PYTHON_ONLY"),
        ],
    )
    def test_run_argument_rewriting(
        self, venv_context: VenvContext, args, expected_rewritten_args
    ):
        """Test run properly rewrites arguments using _rewrite_head."""

        mock_rewrite_head = Mock()
        mock_full_env = Mock(return_value={"VENV": "env"})
        mock_subprocess = Mock()
        mock_completed_process = Mock()
        mock_subprocess.run.return_value = mock_completed_process

        if expected_rewritten_args == "VENV_PYTHON_WITH_ARGS":
            expected_args = [venv_context.executable] + list(args)[1:]
        elif expected_rewritten_args == "VENV_PYTHON_ONLY":
            expected_args = [venv_context.executable]
        else:
            expected_args = expected_rewritten_args

        mock_rewrite_head.return_value = expected_args

        with (
            patch.object(venv_context, "_rewrite_head", mock_rewrite_head),
            patch.object(venv_context, "full_env", mock_full_env),
            patch.object(venv_context.tools, "subprocess", mock_subprocess),
        ):
            result = venv_context.run(args)

            mock_rewrite_head.assert_called_once_with(list(args))

            mock_full_env.assert_called_once_with(None)

            mock_subprocess.run.assert_called_once_with(
                expected_args, env={"VENV": "env"}
            )

            assert result is mock_completed_process

    @pytest.mark.parametrize(
        "env_override, other_kwargs",
        [
            (None, {}),
            ({"CUSTOM": "value"}, {}),
            (None, {"cwd": "/tmp", "timeout": 30}),
            ({"PATH": "/custom"}, {"cwd": "/tmp", "check": True}),
        ],
    )
    def test_run_environment_handling(
        self, venv_context: VenvContext, env_override, other_kwargs
    ):
        """Test run properly handles environment and kwargs."""

        mock_rewrite_head = Mock(return_value=["rewritten", "args"])
        mock_full_env = Mock(return_value={"FULL": "env"})
        mock_subprocess = Mock()
        mock_completed_process = Mock()
        mock_subprocess.run.return_value = mock_completed_process

        kwargs = other_kwargs.copy()
        if env_override is not None:
            kwargs["env"] = env_override

        with (
            patch.object(venv_context, "_rewrite_head", mock_rewrite_head),
            patch.object(venv_context, "full_env", mock_full_env),
            patch.object(venv_context.tools, "subprocess", mock_subprocess),
        ):
            result = venv_context.run(["test"], **kwargs)

            mock_full_env.assert_called_once_with(env_override)

            expected_kwargs = other_kwargs.copy()
            expected_kwargs["env"] = {"FULL": "env"}

            mock_subprocess.run.assert_called_once_with(
                ["rewritten", "args"], **expected_kwargs
            )

            assert result is mock_completed_process

    def test_run_kwargs_env_extraction(self, venv_context: VenvContext):
        """Test run properly extracts env from kwargs without mutation."""
        mock_rewrite_head = Mock(return_value=["args"])
        mock_full_env = Mock(return_value={"MERGED": "env"})
        mock_subprocess = Mock()
        mock_completed_process = Mock()
        mock_subprocess.run.return_value = mock_completed_process

        original_kwargs = {
            "env": {"CUSTOM": "value"},
            "cwd": "/tmp",
            "check": True,
            "capture_output": False,
        }
        kwargs_copy = original_kwargs.copy()

        with (
            patch.object(venv_context, "_rewrite_head", mock_rewrite_head),
            patch.object(venv_context, "full_env", mock_full_env),
            patch.object(venv_context.tools, "subprocess", mock_subprocess),
        ):
            result = venv_context.run(["test"], **original_kwargs)

            assert original_kwargs == kwargs_copy

            mock_full_env.assert_called_once_with({"CUSTOM": "value"})

            expected_call_kwargs = {
                "cwd": "/tmp",
                "check": True,
                "capture_output": False,
                "env": {"MERGED": "env"},
            }
            mock_subprocess.run.assert_called_once_with(
                ["args"], **expected_call_kwargs
            )

            assert result is mock_completed_process
