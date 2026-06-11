from briefcase.integrations.virtual_environment import NoOpEnvManager

from ....utils import create_file


def test_clean(mock_tools, venv_path):
    """The marker file is removed by a clean."""
    create_file(venv_path / "venv_path", "marker contents")
    manager = NoOpEnvManager(mock_tools, venv_path)

    manager.clean()

    assert not manager.marker_path.exists()


def test_noop_when_marker_missing(mock_tools, venv_path):
    """Cleaning is a no-op when there is no marker file."""
    manager = NoOpEnvManager(mock_tools, venv_path)
    assert not manager.marker_path.exists()

    manager.clean()

    assert not manager.marker_path.exists()
