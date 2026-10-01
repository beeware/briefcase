from unittest import mock


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
        "license": "LicenseRef-Other",
        "app_type": "GUI",
        "leftover": "leftover",
    }
    override_input = overrides.copy()
    convert_command.input_project_name = mock.MagicMock(
        wraps=convert_command.input_project_name
    )

    out = convert_command.build_app_context(override_input)

    convert_command.input_project_name.assert_called_once_with(
        "app_name",
        override_value="project_name",
    )
    for k, v in overrides.items():
        if k == "app_type":
            assert not out["console_app"]
        elif k != "leftover":
            assert out[k] == v
    assert "leftover" not in out

    assert override_input == {"leftover": "leftover"}
