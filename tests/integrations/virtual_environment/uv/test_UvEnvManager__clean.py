from ....utils import create_file


def test_clean(venv, mock_tools):
    """Clean removes the venv directory tree when it exists."""
    # Create an existing environment marker
    create_file(venv.venv_path / "pyvenv.cfg", "VENV CONFIG")

    assert venv.exists()

    venv.clean()

    assert not venv.exists()
    assert not venv.venv_path.exists()
