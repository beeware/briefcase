from briefcase.integrations.virtual_environment import NoOpVenvContext

from ...utils import create_file


def test_clean(mock_tools, venv_path):
    """Clean the venv at the specified path."""
    context = NoOpVenvContext(mock_tools, venv_path)

    # Create a venv marker file
    create_file(venv_path / "venv_path", "VENV PATH")

    # Try to clean the venv
    context.clean()

    # Marker file has been deleted
    assert not (venv_path / "venv_path").is_file()


def test_clean_non_existent(mock_tools, venv_path):
    """It's possible to clean a venv that doesn't exist."""

    context = NoOpVenvContext(mock_tools, venv_path)

    # Marker file doesn't exist
    assert not (venv_path / "venv_path").is_file()

    # Try to clean the venv
    context.clean()

    # Marker file still doesn't exist
    assert not (venv_path / "venv_path").is_file()
