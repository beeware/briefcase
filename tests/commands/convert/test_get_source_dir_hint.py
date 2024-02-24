def test_src_is_used_by_default(convert_command):
    module_path = convert_command.base_path / "src" / "module_name"
    module_path.mkdir(parents=True)
    default, info = convert_command.get_source_dir_hint("module-name")
    assert default == str(module_path.relative_to(convert_command.base_path)).replace(
        "\\", "/"
    )
    assert repr(default) in info


def test_flat_is_used_if_src_name_is_wrong(convert_command):
    module_path = convert_command.base_path / "module_name"
    module_path.mkdir(parents=True)
    default, info = convert_command.get_source_dir_hint("module-name")
    assert default == str(module_path.relative_to(convert_command.base_path)).replace(
        "\\", "/"
    )
    assert repr(default) in info


def test_src_child_is_used_if_no_exact_name_is_found(convert_command):
    module_path = convert_command.base_path / "src" / "module_na"
    module_path.mkdir(parents=True)

    # Make a dummy directory that shouldn't be picked
    (convert_command.base_path / "src" / "SOME_DIRECTORY").mkdir()

    # Act and assert
    default, info = convert_command.get_source_dir_hint("module-name")
    assert default == str(module_path.relative_to(convert_command.base_path)).replace(
        "\\", "/"
    )
    assert repr(default) in info


def test_flat_child_is_used_if_no_exact_name_is_found(convert_command):
    module_path = convert_command.base_path / "module_na"
    module_path.mkdir(parents=True)

    # Make a dummy directory that shouldn't be picked
    (convert_command.base_path / "SOME_DIRECTORY").mkdir()

    # Act and assert
    default, info = convert_command.get_source_dir_hint("module-name")
    assert default == str(module_path.relative_to(convert_command.base_path)).replace(
        "\\", "/"
    )
    assert repr(default) in info
