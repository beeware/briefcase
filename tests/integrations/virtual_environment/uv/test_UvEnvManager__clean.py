from briefcase.integrations.virtual_environment import UvVirtualEnvironment

from ....utils import create_file


def test_clean(mock_tools, venv_path):
    """Clean removes the venv directory tree when it exists."""
    create_file(venv_path / "pyvenv.cfg", "VENV CONFIG")
    venv = UvVirtualEnvironment(mock_tools, venv_path)

    assert venv.exists()

    venv.clean()

    assert not venv.exists()
    assert not venv_path.exists()
