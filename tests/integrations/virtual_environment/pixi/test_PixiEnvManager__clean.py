from briefcase.integrations.virtual_environment import PixiVirtualEnvironment

from ....utils import create_file


def test_clean(mock_tools, venv_path):
    """Clean removes the workspace directory tree when it exists."""
    create_file(venv_path / "pixi.toml", "PIXI MANIFEST")
    (venv_path / ".pixi" / "envs" / "default").mkdir(parents=True)
    venv = PixiVirtualEnvironment(mock_tools, venv_path)

    assert venv.exists()

    venv.clean()

    assert not venv.exists()
    assert not venv_path.exists()


def test_clean_no_workspace(mock_tools, venv_path):
    """Clean removes the workspace tree even if the environment is incomplete."""
    venv = PixiVirtualEnvironment(mock_tools, venv_path)
    # The workspace directory is created during prepare(), even though
    # the (mocked) pixi calls don't materialise the environment.
    assert venv_path.exists()

    venv.clean()

    assert not venv_path.exists()
