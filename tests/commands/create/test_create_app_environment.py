import pytest


@pytest.fixture
def create_command(create_command, first_app):
    # Set up the command in a state consistent with a fully verified app config,
    # and a generated template.
    create_command.verify_app(first_app)
    return create_command


def test_create_app_environment(create_command, first_app):
    """By default, the app's environment manager will be used to create the
    environment."""
    venv = create_command.create_app_environment(
        app=first_app,
        platform="some_platform",
        arch="gothic",
    )

    assert venv.env_type == first_app.env_manager
    assert venv.platform == "some_platform"
    assert venv.arch == "gothic"
    assert venv.base_path == create_command.base_path


@pytest.mark.parametrize(
    "env_type",
    [
        "venv",  # An explicit environment manager specification
        "noop",  # Not a valid EnvManagerT value; has special handling
    ],
)
def test_explicit_env_manager(create_command, first_app, env_type):
    """The no-op environment managerapp's environment manager can be overridden."""
    create_command.verify_app(first_app)

    venv = create_command.create_app_environment(
        app=first_app,
        platform="some_platform",
        arch="gothic",
        env_manager=env_type,
    )

    assert venv.env_type == env_type
    assert venv.platform == "some_platform"
    assert venv.arch == "gothic"
    assert venv.base_path == create_command.base_path
