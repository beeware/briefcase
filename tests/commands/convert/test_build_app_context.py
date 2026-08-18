from unittest.mock import MagicMock


def test_overrides_are_used(convert_command):
    (convert_command.base_path / "src/app_name").mkdir(parents=True)
    (convert_command.base_path / "src/app_name/__main__.py").write_text(
        "", encoding="utf-8"
    )
    overrides = {
        "app_name": "app_name",
        "formal_name": "formal_name",
        "source_dir": "src/app_name",
        "test_source_dir": "test_source_dir",
        "project_name": "project_name",
        "description": "description",
        "url": "https://url.com",
        "bundle": "com.bundle",
        "author": "author",
        "author_email": "author_email",
        "license": "Other",
        "app_type": "GUI",
        "leftover": "leftover",
    }
    override_input = overrides.copy()
    out = convert_command.build_app_context(override_input)
    for k, v in overrides.items():
        if k == "app_type":
            assert not out["console_app"]
        elif k != "leftover":
            assert out[k] == v
    assert "leftover" not in out

    assert override_input == {"leftover": "leftover"}


def test_project_name_defaults_to_app_name(convert_command, monkeypatch):
    """If no project_name override is given, the project name defaults to the app name,
    not the formal name."""
    (convert_command.base_path / "src/custom_app").mkdir(parents=True)
    (convert_command.base_path / "src/custom_app/__main__.py").write_text(
        "", encoding="utf-8"
    )

    mock_input_project_name = MagicMock(return_value="mocked-project-name")
    monkeypatch.setattr(convert_command, "input_project_name", mock_input_project_name)

    overrides = {
        "app_name": "custom-app",
        "formal_name": "Custom Formal Name",
        "source_dir": "src/custom_app",
        "test_source_dir": "tests",
        "description": "description",
        "url": "https://url.com",
        "bundle": "com.bundle",
        "author": "author",
        "author_email": "author_email",
        "license": "Other",
        "app_type": "GUI",
    }
    convert_command.build_app_context(overrides.copy())
    mock_input_project_name.assert_called_once_with("custom-app", override_value=None)
    
