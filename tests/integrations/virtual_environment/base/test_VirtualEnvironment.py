from ..conftest import MockVirtualEnvironment


def test_create(first_app, mock_tools, base_venv_path, tmp_path):
    """An environment can be created."""
    venv = MockVirtualEnvironment(
        "forest",
        app=first_app,
        tools=mock_tools,
        base_path=base_venv_path,
        support_path=tmp_path / "support",
        platform="different",
        arch="gothic",
    )

    assert not venv.exists()

    assert venv.app == first_app
    assert venv.tools == mock_tools
    assert venv.name == "forest"
    assert venv.base_path == base_venv_path
    assert venv.venv_path == base_venv_path / ".briefcase/first-app/mock_venv-forest"
    assert venv.support_path == tmp_path / "support"
    assert venv.arch == "gothic"
    assert venv.platform == "different"
