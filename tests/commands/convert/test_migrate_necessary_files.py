from unittest import mock

import pytest

from ...utils import create_file


@pytest.fixture
def dummy_app_name():
    return "app_name"


@pytest.fixture
def project_dir_with_files(tmp_path, dummy_app_name):
    # Setup dummy files created by calling new_app
    out_dir = tmp_path / dummy_app_name
    out_dir.mkdir()

    pyproject_content = """
[tool.briefcase]
placeholder = "abc"
"""
    create_file(out_dir / "pyproject.toml", pyproject_content)
    create_file(out_dir / "CHANGELOG", "CHANGELOG")
    create_file(out_dir / "LICENSE", "LICENSE")
    create_file(out_dir / f"tests/{dummy_app_name}.py", "test entry script")
    create_file(out_dir / "tests/test_dummy.py", "tests")
    create_file(out_dir / f"src/{dummy_app_name}/{dummy_app_name}.py", "entry point")
    return out_dir


def test_empty_test_source_dir(convert_command, project_dir_with_files, dummy_app_name):
    """The full tests dir is copied if no test_source_dir is given."""
    convert_command.migrate_necessary_files(
        project_dir_with_files, "test", dummy_app_name
    )

    dummy_tests = convert_command.base_path / "test/test_dummy.py"
    assert dummy_tests.is_file()
    assert dummy_tests.read_text() == "tests"

    test_entry_script = convert_command.base_path / f"test/{dummy_app_name}.py"
    assert test_entry_script.is_file()
    assert test_entry_script.read_text() == "test entry script"


def test_provided_test_source_dir(
    convert_command, project_dir_with_files, dummy_app_name
):
    """Only the test_entry_script is copied if test_source_dir is given."""
    test_source_dir = "tests"
    full_test_path = convert_command.base_path / test_source_dir
    full_test_path.mkdir(parents=True)
    convert_command.migrate_necessary_files(
        project_dir_with_files, test_source_dir, dummy_app_name
    )

    dummy_tests = full_test_path / "test_dummy.py"
    assert not dummy_tests.is_file()

    test_entry_script = full_test_path / f"{dummy_app_name}.py"
    assert test_entry_script.is_file()
    assert test_entry_script.read_text() == "test entry script"


def test_nondefault_test_source_dir(
    convert_command, project_dir_with_files, dummy_app_name
):
    """The test_entry_script is copied to the correct directory if test_source_dir is
    given."""
    test_source_dir = "tests_dir"
    full_test_path = convert_command.base_path / test_source_dir
    full_test_path.mkdir(parents=True)

    convert_command.migrate_necessary_files(
        project_dir_with_files, test_source_dir, dummy_app_name
    )

    dummy_tests = full_test_path / "test_dummy.py"
    assert not dummy_tests.is_file()

    test_entry_script = full_test_path / f"{project_dir_with_files.name}.py"
    assert test_entry_script.is_file()
    assert test_entry_script.read_text() == "test entry script"


def test_warning_without_license_file(
    convert_command, project_dir_with_files, dummy_app_name
):
    """A single warning is raised if changelog file is present but not license file."""
    convert_command.logger.warning = mock.MagicMock()
    test_source_dir = ""

    create_file(convert_command.base_path / "CHANGELOG", "")
    convert_command.migrate_necessary_files(
        project_dir_with_files, test_source_dir, dummy_app_name
    )

    convert_command.logger.warning.assert_called_once_with(
        f"License file not found in {convert_command.base_path}. Creating a template LICENSE file."
    )


def test_pep621_wrong_license_filename(
    convert_command, project_dir_with_files, dummy_app_name
):
    convert_command.logger.warning = mock.MagicMock()
    test_source_dir = ""
    license_name = "LICENSE.txt"
    create_file(convert_command.base_path / license_name, "")
    create_file(
        convert_command.base_path / "pyproject.toml",
        f'[project]\nlicense = {{ file = "{license_name}" }}',
    )
    create_file(convert_command.base_path / "CHANGELOG", "")
    convert_command.migrate_necessary_files(
        project_dir_with_files, test_source_dir, dummy_app_name
    )
    convert_command.logger.warning.assert_called_once_with(
        f"License file found in {convert_command.base_path}, but its name is {license_name} not LICENSE. "
        "Creating a template LICENSE file, but you might want to consider renaming the file you have."
    )


def test_warning_without_changelog_file(
    convert_command, project_dir_with_files, dummy_app_name
):
    """A single warning is raised if license file is present but not changelog file."""
    convert_command.logger.warning = mock.MagicMock()

    test_source_dir = ""

    create_file(convert_command.base_path / "LICENSE", "")
    convert_command.migrate_necessary_files(
        project_dir_with_files, test_source_dir, dummy_app_name
    )

    convert_command.logger.warning.assert_called_once_with(
        f"Changelog file not found in {convert_command.base_path}. You should either create a new changelog file in"
        f" {convert_command.base_path} or rename an already existing changelog file to CHANGELOG."
    )


def test_no_warning_with_license_and_changelog_file(
    convert_command, project_dir_with_files, dummy_app_name
):
    """No warning is raised if both license file and changelog file is present."""
    convert_command.logger.warning = mock.MagicMock()

    test_source_dir = ""

    create_file(convert_command.base_path / "LICENSE", "")
    create_file(convert_command.base_path / "CHANGELOG", "")
    convert_command.migrate_necessary_files(
        project_dir_with_files, test_source_dir, dummy_app_name
    )

    convert_command.logger.warning.assert_not_called()


def test_two_warnings_without_license_and_changelog_file(
    convert_command, project_dir_with_files, dummy_app_name
):
    """Two warnings are raised if both license file and changelog file are missing."""
    convert_command.logger.warning = mock.MagicMock()

    test_source_dir = ""

    convert_command.migrate_necessary_files(
        project_dir_with_files, test_source_dir, dummy_app_name
    )
    license_warning = f"License file not found in {convert_command.base_path}. Creating a template LICENSE file."
    changelog_warning = (
        f"Changelog file not found in {convert_command.base_path}. You should either create a new changelog file in"
        f" {convert_command.base_path} or rename an already existing changelog file to CHANGELOG."
    )
    assert convert_command.logger.warning.mock_calls == [
        mock.call(license_warning),
        mock.call(changelog_warning),
    ]
