import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_src_is_used_by_default(convert_command):
    module_path = convert_command.base_path / "src" / "module_name"
    module_path.mkdir(parents=True)
    default, info = convert_command.get_source_dir_hint("module-name", "module_name")
    assert default == str(module_path.relative_to(convert_command.base_path)).replace(
        "\\", "/"
    )
    assert repr(default) in info


def test_flat_is_used_if_src_name_is_wrong(convert_command):
    module_path = convert_command.base_path / "module_name"
    module_path.mkdir(parents=True)
    default, info = convert_command.get_source_dir_hint("module-name", "module_name")
    assert default == str(module_path.relative_to(convert_command.base_path)).replace(
        "\\", "/"
    )
    assert repr(default) in info


def test_fallback_is_used_if_no_src_or_flat(convert_command):
    module_path = convert_command.base_path / "something/module_name"
    module_path.mkdir(parents=True)
    default, info = convert_command.get_source_dir_hint("module-name", "module_name")
    assert default == str(module_path.relative_to(convert_command.base_path)).replace(
        "\\", "/"
    )
    assert repr(default) in info


def test_src_is_preferred_over_flat(convert_command):
    module_path = convert_command.base_path / "src" / "module_name"
    module_path.mkdir(parents=True)
    flat_module_path = convert_command.base_path / "module_name"
    flat_module_path.mkdir(parents=True)
    default, info = convert_command.get_source_dir_hint("module-name", "module_name")
    assert default == str(module_path.relative_to(convert_command.base_path)).replace(
        "\\", "/"
    )
    assert repr(default) in info
    assert repr(flat_module_path) not in info


def test_flat_is_preferred_over_fallback(convert_command):
    module_path = convert_command.base_path / "module_name"
    module_path.mkdir(parents=True)
    fallback_module_path = convert_command.base_path / "something/module_name"
    fallback_module_path.mkdir(parents=True)
    default, info = convert_command.get_source_dir_hint("module-name", "module_name")
    assert default == str(module_path.relative_to(convert_command.base_path)).replace(
        "\\", "/"
    )
    assert repr(default) in info
    assert repr(fallback_module_path) not in info


def test_flat_is_used_if_src_is_wrong(convert_command):
    module_path = convert_command.base_path / "module_name"
    module_path.mkdir(parents=True)
    wrong_module_path = convert_command.base_path / "src" / "different_module_name"
    wrong_module_path.mkdir(parents=True)
    default, info = convert_command.get_source_dir_hint("module-name", "module_name")
    assert default == str(module_path.relative_to(convert_command.base_path)).replace(
        "\\", "/"
    )
    assert repr(default) in info
    assert repr(module_path.name) in info


def test_exception_is_raised_if_no_source_dir(convert_command):
    module_path = convert_command.base_path / "src" / "different_module_name"
    module_path.mkdir(parents=True)
    with pytest.raises(BriefcaseCommandError):
        convert_command.get_source_dir_hint("module-name", "module_name")
