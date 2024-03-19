def test_missing_pyproject_file(convert_command):
    """An empty dict is returned if there is no pyproject file."""
    assert not (convert_command.base_path / "pyproject.toml").exists()
    assert convert_command.pyproject == {}


def test_present_pyproject_file(convert_command):
    """The pyproject.toml file is loaded if it is present."""
    (convert_command.base_path / "pyproject.toml").write_text(
        '[project]\nname="project-name"', encoding="utf-8"
    )
    assert convert_command.pyproject == {"project": {"name": "project-name"}}
