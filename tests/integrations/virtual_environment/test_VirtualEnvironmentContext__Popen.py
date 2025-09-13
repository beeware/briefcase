from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_subprocess_setup(venv_context, monkeypatch):
    """Setup mock objects for subprocess testing."""
    mock_rewrite_head = Mock(return_value=["rewritten", "args"])
    mock_full_env = Mock(return_value={"FULL": "env"})
    mock_subprocess = Mock()
    mock_popen_instance = Mock()
    mock_subprocess.Popen.return_value = mock_popen_instance

    monkeypatch.setattr(venv_context, "_rewrite_head", mock_rewrite_head)
    monkeypatch.setattr(venv_context, "full_env", mock_full_env)
    monkeypatch.setattr(venv_context.tools, "subprocess", mock_subprocess)

    return {
        "mock_rewrite_head": mock_rewrite_head,
        "mock_full_env": mock_full_env,
        "mock_subprocess": mock_subprocess,
        "mock_popen_instance": mock_popen_instance,
    }


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
    venv_context,
    mock_subprocess_setup,
    env_override,
    other_kwargs,
):
    """Test Popen properly handles environment and kwargs without mutating input."""
    mocks = mock_subprocess_setup

    kwargs = other_kwargs.copy()
    if env_override is not None:
        kwargs["env"] = env_override

    # Keep original for mutation check
    original_kwargs = kwargs.copy()

    result = venv_context.Popen(["test"], **kwargs)

    # Verify no mutation of input kwargs
    assert kwargs == original_kwargs

    # Verify method calls
    mocks["mock_rewrite_head"].assert_called_once_with(["test"])
    mocks["mock_full_env"].assert_called_once_with(env_override)

    # Verify subprocess.Popen call
    expected_kwargs = other_kwargs.copy()
    expected_kwargs["env"] = {"FULL": "env"}

    mocks["mock_subprocess"].Popen.assert_called_once_with(
        ["rewritten", "args"], **expected_kwargs
    )

    assert result is mocks["mock_popen_instance"]


def test_popen_no_args(venv_context, mock_subprocess_setup):
    """Test Popen handles empty args list."""
    mocks = mock_subprocess_setup
    mocks["mock_rewrite_head"].return_value = []

    result = venv_context.Popen([])

    mocks["mock_rewrite_head"].assert_called_once_with([])
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

    result = venv_context.Popen(["/usr/bin/python", "-m", "pip", "install", "package"])

    mocks["mock_rewrite_head"].assert_called_once_with(
        ["/usr/bin/python", "-m", "pip", "install", "package"]
    )
    mocks["mock_full_env"].assert_called_once_with(None)
    mocks["mock_subprocess"].Popen.assert_called_once_with(
        ["/venv/bin/python", "-m", "pip", "install", "package"], env={"FULL": "env"}
    )

    assert result is mocks["mock_popen_instance"]
