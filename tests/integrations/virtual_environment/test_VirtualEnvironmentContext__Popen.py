import pytest
from test_utils import (
    ENVIRONMENT_TEST_PARAMS,
    assert_environment_handling,
    assert_no_kwargs_mutation,
    assert_rewrite_head_called,
)


@pytest.mark.parametrize("env_override, other_kwargs", ENVIRONMENT_TEST_PARAMS)
def test_popen_environment_handling(
    venv_context, mock_subprocess_setup, env_override, other_kwargs
):
    """Test Popen properly handles environment and kwargs without mutating input."""
    mocks = mock_subprocess_setup

    kwargs = other_kwargs.copy()
    if env_override is not None:
        kwargs["env"] = env_override

    original_kwargs = kwargs.copy()

    result = venv_context.Popen(["test"], **kwargs)

    assert_no_kwargs_mutation(kwargs, original_kwargs)

    assert_rewrite_head_called(mocks["mock_rewrite_head"], ["test"])

    assert_environment_handling(
        mock_full_env=mocks["mock_full_env"],
        env_override=env_override,
        mock_method=mocks["mock_subprocess"].Popen,
        method_args=["rewritten", "args"],
        other_kwargs=other_kwargs,
    )

    assert result is mocks["mock_popen_instance"]


def test_popen_no_args(venv_context, mock_subprocess_setup):
    """Test Popen handles empty args list."""
    mocks = mock_subprocess_setup
    mocks["mock_rewrite_head"].return_value = []

    result = venv_context.Popen([])

    assert_rewrite_head_called(mocks["mock_rewrite_head"], [])
    mocks["mock_full_env"].assert_called_once_with(None)
    mocks["mock_subprocess"].Popen.assert_called_once_with([], env={"FULL": "env"})

    assert result is mocks["mock_popen_instance"]


def test_popen_complex_args_rewriting(venv_context, mock_subprocess_setup):
    """Test Popen handles complex argument rewriting."""
    mocks = mock_subprocess_setup
    mocks["mock_rewrite_head"].return_value = [
        "/venv/bin/python",
        "-m",
        "pip",
        "install",
        "package",
    ]

    original_args = ["/usr/bin/python", "-m", "pip", "install", "package"]
    result = venv_context.Popen(original_args)

    assert_rewrite_head_called(mocks["mock_rewrite_head"], original_args)
    mocks["mock_full_env"].assert_called_once_with(None)
    mocks["mock_subprocess"].Popen.assert_called_once_with(
        ["/venv/bin/python", "-m", "pip", "install", "package"], env={"FULL": "env"}
    )

    assert result is mocks["mock_popen_instance"]
