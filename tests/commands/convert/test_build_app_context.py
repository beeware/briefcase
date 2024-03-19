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
        "leftover": "leftover",
    }
    override_input = overrides.copy()
    out = convert_command.build_app_context(override_input)
    for k, v in overrides.items():
        if k != "leftover":
            assert out[k] == v
    assert "leftover" not in out

    assert override_input == {"leftover": "leftover"}
