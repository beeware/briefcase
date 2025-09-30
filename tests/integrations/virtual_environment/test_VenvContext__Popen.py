import pytest

from tests.integrations.virtual_environment.utils import (
    ENVIRONMENT_TEST_PARAMS,
    assert_environment_handling,
)


@pytest.mark.parametrize("env_override, other_kwargs", ENVIRONMENT_TEST_PARAMS)
def test_popen_environment_handling(
    venv_context,
    mock_subprocess_setup,
    env_override,
    other_kwargs,
):
    """Popen properly handles environment and kwargs without mutating input."""
    mocks = mock_subprocess_setup

    kwargs = other_kwargs.copy()
    if env_override is not None:
        kwargs["env"] = env_override

    original_kwargs = kwargs.copy()

    result = venv_context.Popen(["test"], **kwargs)

    assert kwargs == original_kwargs
    mocks["rewrite_head"].assert_called_once_with(["test"])

    assert_environment_handling(
        mock_full_env=mocks["full_env"],
        env_override=env_override,
        mock_method=mocks["subprocess"].Popen,
        method_args=["rewritten", "args"],
        other_kwargs=other_kwargs,
    )

    assert result is mocks["popen_instance"]


def test_popen_no_args(venv_context, mock_subprocess_setup):
    """Popen handles empty args list."""
    mocks = mock_subprocess_setup
    mocks["rewrite_head"].return_value = []

    result = venv_context.Popen([])

    mocks["rewrite_head"].assert_called_once_with([])
    mocks["full_env"].assert_called_once_with(None)
    mocks["subprocess"].Popen.assert_called_once_with([], env={"FULL": "env"})

    assert result is mocks["popen_instance"]


def test_popen_complex_args_rewriting(venv_context, mock_subprocess_setup):
    """Popen handles complex argument rewriting."""
    mocks = mock_subprocess_setup
    mocks["rewrite_head"].return_value = [
        "/venv/bin/python",
        "-m",
        "pip",
        "install",
        "package",
    ]

    original_args = ["/usr/bin/python", "-m", "pip", "install", "package"]
    result = venv_context.Popen(original_args)

    mocks["rewrite_head"].assert_called_once_with(original_args)
    mocks["full_env"].assert_called_once_with(None)
    mocks["subprocess"].Popen.assert_called_once_with(
        ["/venv/bin/python", "-m", "pip", "install", "package"], env={"FULL": "env"}
    )

    assert result is mocks["popen_instance"]
