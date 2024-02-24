def test_pep621_data_is_used(convert_command):
    """The PEP621-description is used if present."""
    (convert_command.base_path / "pyproject.toml").write_text(
        '[project]\ndescription="Some description"'
    )
    assert convert_command.input_description(None) == "Some description"


def test_override_is_used(convert_command):
    """The override is used even if a PEP621-description is present."""
    (convert_command.base_path / "pyproject.toml").write_text(
        '[project]\ndescription="Some description"'
    )
    assert convert_command.input_description("OVERRIDE TEXT") == "OVERRIDE TEXT"
