import pytest

from ...utils import create_file


def test_valid_test_source_dir(convert_command):
    """Valid test_source_dir raises no errors and returns True."""
    app_name = "newtarget"
    test_source_dir = "tests"

    full_test_source_dir = convert_command.base_path / test_source_dir
    full_test_source_dir.mkdir(parents=True)

    assert convert_command.validate_test_source_dir(app_name, test_source_dir)


def test_test_source_dir_shouldnt_contain_test_entry_script(convert_command):
    """If `convert_command.base_path/test_source_dir` already contains a test entry
    script, a ValueError is raised."""
    app_name = "newtarget"
    test_source_dir = "tests"

    test_entry_path = convert_command.base_path / test_source_dir / f"{app_name}.py"
    create_file(test_entry_path, "TEST ENTRY SCRIPT")

    with pytest.raises(ValueError):
        convert_command.validate_test_source_dir(app_name, test_source_dir)
