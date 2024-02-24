import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_pyproject_file(convert_command):
    convert_command.validate_pyproject_file()


def test_briefcase_field_present(convert_command):
    (convert_command.base_path / "pyproject.toml").write_text(
        "[tool.briefcase]\n", encoding="utf-8"
    )
    with pytest.raises(BriefcaseCommandError):
        convert_command.validate_pyproject_file()


def test_no_briefcase_field(convert_command):
    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n", encoding="utf-8"
    )
    convert_command.validate_pyproject_file()
