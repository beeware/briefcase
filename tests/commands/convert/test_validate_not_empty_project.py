import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_empty_project(convert_command):
    with pytest.raises(BriefcaseCommandError):
        convert_command.validate_not_empty_project()


@pytest.mark.parametrize("logdir_name", ["log", "logs", "something"])
def test_only_log_directory(convert_command, logdir_name):
    (convert_command.base_path / f"{logdir_name}").mkdir()
    (convert_command.base_path / f"{logdir_name}/something.log").write_text(
        "", encoding="utf-8"
    )

    with pytest.raises(BriefcaseCommandError):
        convert_command.validate_not_empty_project()


def no_fail_with_nonempty_project(convert_command):
    (convert_command.base_path / "app_name").mkdir()
    (convert_command.base_path / "app_name/something.py").write_text(
        "", encoding="utf-8"
    )
    convert_command.validate_not_empty_project()
