def test_pep621_data_is_used(convert_command):
    """The PEP621-description is used if present."""
    (convert_command.base_path / "pyproject.toml").write_text(
        '[project]\ndescription="Some description"', encoding="utf-8"
    )
    assert convert_command.input_description(None) == "Some description"


def test_override_is_used(convert_command):
    """The override is used even if a PEP621-description is present."""
    (convert_command.base_path / "pyproject.toml").write_text(
        '[project]\ndescription="Some description"', encoding="utf-8"
    )
    assert convert_command.input_description("OVERRIDE TEXT") == "OVERRIDE TEXT"


def test_prompted_description(convert_command):
    """The user is prompted for a description if there is no description in the
    pyproject.toml file."""
    convert_command.input.values = ["A very descriptive description"]
    assert convert_command.input_description(None) == "A very descriptive description"
