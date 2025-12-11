from briefcase.integrations.virtual_environment import VenvContext

from ...utils import create_file


def test_clean(mock_tools, venv_path):
    """Clean the venv at the specified path."""
    context = VenvContext(mock_tools, venv_path)

    # Create a dummy venv configuration
    create_file(venv_path / "pyvenv.cfg", "VENV CONFIG")

    # venv exists before clean
    assert context.exists()

    # Try to clean the venv
    context.clean()

    # venv doesn't exist before clean
    assert not context.exists()


def test_clean_non_existent(mock_tools, venv_path):
    """It's possible to clean a venv that doesn't exist."""

    context = VenvContext(mock_tools, venv_path)

    # venv doesn't exist before clean
    assert not context.exists()

    # Try to clean the venv
    context.clean()

    # venv doesn't exist before clean
    assert not context.exists()
