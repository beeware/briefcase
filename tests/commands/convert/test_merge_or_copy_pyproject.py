import tomli_w

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def test_copy_pyproject_toml(convert_command, tmp_path):
    base_config_file = convert_command.base_path / "pyproject.toml"
    briefcase_config_file = tmp_path / "input" / "pyproject.toml"

    briefcase_config_file.parent.mkdir(parents=True)
    briefcase_config_file.write_text("placeholder", encoding="utf-8")
    convert_command.merge_or_copy_pyproject(briefcase_config_file)

    assert base_config_file.is_file()
    with open(base_config_file, encoding="utf-8") as file:
        assert file.read() == "placeholder"


def test_merge_pyproject(convert_command, tmp_path):
    base_config_file = convert_command.base_path / "pyproject.toml"
    briefcase_config_file = tmp_path / "input" / "pyproject.toml"

    base_config_content = {"placeholder1": "a"}
    briefcase_config_content = {"placeholder2": "b"}
    merged_dict = {**base_config_content, **briefcase_config_content}

    with open(base_config_file, "wb") as file:
        tomli_w.dump(base_config_content, file)

    briefcase_config_file.parent.mkdir(parents=True)
    with open(briefcase_config_file, "wb") as file:
        tomli_w.dump(briefcase_config_content, file)

    convert_command.merge_or_copy_pyproject(briefcase_config_file)

    merged_content = base_config_file.read_text(encoding="utf-8")
    assert merged_dict == tomllib.loads(merged_content)
