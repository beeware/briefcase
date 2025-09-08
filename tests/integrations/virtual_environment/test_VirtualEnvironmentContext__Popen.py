from unittest.mock import Mock, patch

import pytest

from briefcase.integrations.virtual_environment import VenvContext


class TestPopen:
    """Test cases for VenvContext.Popen method."""

    @pytest.mark.parametrize(
        "env_override, other_kwargs",
        [
            (None, {}),
            ({"CUSTOM": "value"}, {}),
            (None, {"cwd": "/tmp", "stdout": "subprocess.PIPE"}),
            (
                {"PATH": "/custom"},
                {"stdin": "subprocess.PIPE", "stderr": "subprocess.STDOUT"},
            ),
        ],
    )
    def test_popen_environment_handling(
        self, venv_context: VenvContext, env_override, other_kwargs
    ):
        """Test Popen properly handles environment and kwargs."""

        mock_rewrite_head = Mock(return_value=["rewritten", "args"])
        mock_full_env = Mock(return_value={"FULL": "env"})
        mock_subprocess = Mock()
        mock_popen_instance = Mock()
        mock_subprocess.Popen.return_value = mock_popen_instance

        kwargs = other_kwargs.copy()
        if env_override is not None:
            kwargs["env"] = env_override

        with (
            patch.object(venv_context, "_rewrite_head", mock_rewrite_head),
            patch.object(venv_context, "full_env", mock_full_env),
            patch.object(venv_context.tools, "subprocess", mock_subprocess),
        ):
            result = venv_context.Popen(["test"], **kwargs)

            mock_full_env.assert_called_once_with(env_override)

            expected_kwargs = other_kwargs.copy()
            expected_kwargs["env"] = {"FULL": "env"}

            mock_subprocess.Popen.assert_called_once_with(
                ["rewritten", "args"], **expected_kwargs
            )

            assert result is mock_popen_instance

    def test_popen_kwargs_env_extraction(self, venv_context: VenvContext):
        """Test Popen properly extracts env from kwargs without mutation."""
        mock_rewrite_head = Mock(return_value=["args"])
        mock_full_env = Mock(return_value={"MERGED": "env"})
        mock_subprocess = Mock()
        mock_popen_instance = Mock()
        mock_subprocess.Popen.return_value = mock_popen_instance

        original_kwargs = {
            "env": {"CUSTOM": "value"},
            "cwd": "/tmp",
            "stdout": "subprocess.PIPE",
            "stderr": "subprocess.PIPE",
        }
        kwargs_copy = original_kwargs.copy()

        with (
            patch.object(venv_context, "_rewrite_head", mock_rewrite_head),
            patch.object(venv_context, "full_env", mock_full_env),
            patch.object(venv_context.tools, "subprocess", mock_subprocess),
        ):
            result = venv_context.Popen(["test"], **original_kwargs)

            assert original_kwargs == kwargs_copy

            mock_full_env.assert_called_once_with({"CUSTOM": "value"})

            expected_call_kwargs = {
                "cwd": "/tmp",
                "stdout": "subprocess.PIPE",
                "stderr": "subprocess.PIPE",
                "env": {"MERGED": "env"},
            }
            mock_subprocess.Popen.assert_called_once_with(
                ["args"], **expected_call_kwargs
            )

            assert result is mock_popen_instance
