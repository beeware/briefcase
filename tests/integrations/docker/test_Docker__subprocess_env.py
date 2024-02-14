import pytest


@pytest.mark.parametrize(
    "env, subprocess_env",
    [
        (None, {"DOCKER_CLI_HINTS": "false"}),
        ({}, {"DOCKER_CLI_HINTS": "false"}),
        ({"ENV_VAR": "VALUE"}, {"ENV_VAR": "VALUE", "DOCKER_CLI_HINTS": "false"}),
        (
            {"ENV_VAR": "VALUE", "DOCKER_CLI_HINTS": "true"},
            {
                "ENV_VAR": "VALUE",
                "DOCKER_CLI_HINTS": "true",
            },
        ),
    ],
)
@pytest.mark.usefixtures("mock_docker")
def test_subprocess_env(mock_tools, env, subprocess_env):
    """The env for subprocess calls is set properly."""
    assert mock_tools.docker.subprocess_env(env) == subprocess_env
