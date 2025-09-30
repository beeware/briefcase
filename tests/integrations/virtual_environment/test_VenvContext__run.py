import pytest

from tests.integrations.virtual_environment.utils import (
    ENVIRONMENT_TEST_PARAMS,
    assert_environment_handling,
)


@pytest.mark.parametrize("env_override, other_kwargs", ENVIRONMENT_TEST_PARAMS)
def test_run_environment_handling(
    venv_context,
    mock_subprocess_setup,
    env_override,
    other_kwargs,
):
    """Run merges venv with overrides and passes all kwargs to subprocess."""
    mocks = mock_subprocess_setup

    kwargs = other_kwargs.copy()
    if env_override is not None:
        kwargs["env"] = env_override

    original_kwargs = kwargs.copy()

    result = venv_context.run(["test"], **kwargs)

    assert kwargs == original_kwargs
    mocks["rewrite_head"].assert_called_once_with(["test"])

    # The venv's full_env should be called with any provided env override, and the
    # resulting environment should be passed to subprocess.check_output along with other
    # kwargs unchanged.
    assert_environment_handling(
        mock_full_env=mocks["full_env"],
        env_override=env_override,
        mock_method=mocks["subprocess"].run,
        method_args=["rewritten", "args"],
        other_kwargs=other_kwargs,
    )

    assert result is mocks["subprocess"].run.return_value


def test_run_kwargs_env_extraction(venv_context, mock_subprocess_setup):
    """Run extracts env from kwargs without modifying the original kwargs."""
    mocks = mock_subprocess_setup

    original_kwargs = {
        "env": {"CUSTOM": "value"},
        "cwd": "/tmp",
        "check": True,
        "capture_output": False,
    }
    kwargs_copy = original_kwargs.copy()

    result = venv_context.run(["test"], **original_kwargs)

    # The original kwargs dict should remain unchanged
    assert original_kwargs == kwargs_copy

    # The env value is passed to full_env()
    mocks["full_env"].assert_called_once_with({"CUSTOM": "value"})

    # The resulting merged environment replaces the original env in the subprocess call.
    expected_call_kwargs = {
        "cwd": "/tmp",
        "check": True,
        "capture_output": False,
        "env": {"FULL": "env"},
    }
    mocks["subprocess"].run.assert_called_once_with(
        ["rewritten", "args"], **expected_call_kwargs
    )

    assert result is mocks["subprocess"].run.return_value
