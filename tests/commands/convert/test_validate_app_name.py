import pytest


@pytest.mark.parametrize(
    "name",
    [
        "helloworld",
        "existing",
    ],
)
def test_valid_app_name(convert_command, name, tmp_path):
    """Test that valid app names are accepted, including pre-existing names."""
    (tmp_path / "existing").mkdir()

    # This is mostly tested by the equivalent test for the `new` command;
    # This test exists for a check that basic functionality still exists,
    # despite the other overrides.
    assert convert_command.validate_app_name(name)
