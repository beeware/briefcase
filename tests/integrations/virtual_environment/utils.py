ENVIRONMENT_TEST_PARAMS = [
    (None, {}),
    ({"CUSTOM": "value"}, {}),
    (None, {"cwd": "/tmp", "timeout": 30}),
    ({"PATH": "/custom"}, {"cwd": "/tmp", "check": True}),
]


def assert_environment_handling(
    mock_full_env,
    env_override,
    mock_method,
    method_args,
    other_kwargs,
):
    """Assert proper environment handling in subprocess calls."""
    mock_full_env.assert_called_once_with(env_override)

    expected_kwargs = other_kwargs.copy()
    expected_kwargs["env"] = {"FULL": "env"}

    mock_method.assert_called_once_with(method_args, **expected_kwargs)
