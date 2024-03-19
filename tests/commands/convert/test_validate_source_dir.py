import pytest


def test_valid_source_dir(convert_command):
    """Valid source_dir raises no errors and returns True."""
    module_name = "myapplication"
    source_dir = f"src/{module_name}"

    full_source_dir = convert_command.base_path / source_dir
    full_source_dir.mkdir(parents=True)
    (full_source_dir / "__main__.py").write_text("", encoding="utf-8")

    assert convert_command.validate_source_dir(module_name, source_dir)


def test_wrong_source_dir_name(convert_command):
    """source_dir with wrong name raises ValueError."""
    module_name = "myapplication"
    source_dir = f"src/{module_name}"

    full_source_dir = convert_command.base_path / source_dir
    full_source_dir.mkdir(parents=True)

    with pytest.raises(ValueError):
        convert_command.validate_source_dir("wrong_name", source_dir)


def test_source_dir_no_entry_point(convert_command):
    """source_dir without __main__.py raises ValueError."""
    module_name = "myapplication"
    source_dir = f"src/{module_name}"

    (convert_command.base_path / source_dir).mkdir(parents=True)
    with pytest.raises(ValueError):
        convert_command.validate_source_dir(module_name, source_dir)


def test_source_dir_does_not_exist(convert_command):
    """source_dir raises value error if {target}/{source_dir} doesn't exist."""
    module_name = "myapplication"
    source_dir = f"src/{module_name}"

    with pytest.raises(ValueError):
        convert_command.validate_source_dir(module_name, source_dir)
