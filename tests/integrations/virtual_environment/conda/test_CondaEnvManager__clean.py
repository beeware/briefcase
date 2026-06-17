from briefcase.integrations.virtual_environment import CondaVirtualEnvironment

from ....utils import create_file


def test_clean(mock_tools, venv_path):
    """Clean removes the environment directory tree when it exists."""
    create_file(venv_path / "conda-meta" / "history", "HISTORY")
    venv = CondaVirtualEnvironment(mock_tools, venv_path)

    assert venv.exists()

    venv.clean()

    assert not venv.exists()
    assert not venv_path.exists()


def test_clean_no_environment(mock_tools, venv_path):
    """Clean is a no-op when the environment doesn't exist."""
    venv = CondaVirtualEnvironment(mock_tools, venv_path)

    assert not venv.exists()

    venv.clean()

    assert not venv_path.exists()
