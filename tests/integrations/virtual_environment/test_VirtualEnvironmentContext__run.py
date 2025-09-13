import pytest
from test_utils import (
    ENVIRONMENT_TEST_PARAMS,
    assert_environment_handling,
    assert_no_kwargs_mutation,
)


@pytest.mark.parametrize("env_override, other_kwargs", ENVIRONMENT_TEST_PARAMS)
def test_run_environment_handling(
    venv_context, mock_subprocess_setup, env_override, other_kwargs
):
    """Test run properly handles environment and kwargs."""
    mocks = mock_subprocess_setup

    kwargs = other_kwargs.copy()
    if env_override is not None:
        kwargs["env"] = env_override

    result = venv_context.run(["test"], **kwargs)

    assert_environment_handling(
        mock_full_env=mocks["mock_full_env"],
        env_override=env_override,
        mock_method=mocks["mock_subprocess"].run,
        method_args=["rewritten", "args"],
        other_kwargs=other_kwargs,
    )

    assert result is mocks["mock_subprocess"].run.return_value


def test_run_kwargs_env_extraction(venv_context, mock_subprocess_setup):
    """Test run properly extracts env from kwargs without mutation."""
    mocks = mock_subprocess_setup

    original_kwargs = {
        "env": {"CUSTOM": "value"},
        "cwd": "/tmp",
        "check": True,
        "capture_output": False,
    }
    kwargs_copy = original_kwargs.copy()

    result = venv_context.run(["test"], **original_kwargs)

    assert_no_kwargs_mutation(original_kwargs, kwargs_copy)

    mocks["mock_full_env"].assert_called_once_with({"CUSTOM": "value"})

    expected_call_kwargs = {
        "cwd": "/tmp",
        "check": True,
        "capture_output": False,
        "env": {"FULL": "env"},
    }
    mocks["mock_subprocess"].run.assert_called_once_with(
        ["rewritten", "args"], **expected_call_kwargs
    )

    assert result is mocks["mock_subprocess"].run.return_value
