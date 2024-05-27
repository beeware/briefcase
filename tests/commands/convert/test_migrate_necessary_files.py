from unittest import mock

import pytest

from ...utils import create_file


@pytest.fixture
def dummy_app_name():
    return "app_name"


@pytest.fixture
def project_dir_with_files(tmp_path, dummy_app_name, test_source_dir):
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
    create_file(out_dir / test_source_dir / f"{dummy_app_name}.py", "test entry script")
    create_file(out_dir / test_source_dir / "test_dummy.py", "dummy tests")
    create_file(out_dir / f"src/{dummy_app_name}/{dummy_app_name}.py", "entry point")
    return out_dir


@pytest.mark.parametrize("test_source_dir", ["test", "tests", "othertest"])
def test_empty_test_source_dir(
    convert_command,
    project_dir_with_files,
    dummy_app_name,
    test_source_dir,
):
    """The full tests dir is copied if no test_source_dir is given."""
    convert_command.migrate_necessary_files(
        project_dir_with_files,
        test_source_dir,
        dummy_app_name,
    )

    dummy_tests = convert_command.base_path / test_source_dir / "test_dummy.py"
    assert dummy_tests.is_file()
    assert dummy_tests.read_text(encoding="utf-8") == "dummy tests"

    test_entry_script = (
        convert_command.base_path / test_source_dir / f"{dummy_app_name}.py"
    )
    assert test_entry_script.is_file()
    assert test_entry_script.read_text(encoding="utf-8") == "test entry script"


@pytest.mark.parametrize("test_source_dir", ["test", "tests", "othertest"])
def test_provided_test_source_dir(
    convert_command,
    project_dir_with_files,
    dummy_app_name,
    test_source_dir,
):
    """Only the test_entry_script is copied if test_source_dir is given."""
    full_test_path = convert_command.base_path / test_source_dir
    full_test_path.mkdir(parents=True)
    convert_command.migrate_necessary_files(
        project_dir_with_files,
        test_source_dir,
        dummy_app_name,
    )

    dummy_tests = full_test_path / "test_dummy.py"
    assert not dummy_tests.is_file()

    test_entry_script = full_test_path / f"{dummy_app_name}.py"
    assert test_entry_script.is_file()
    assert test_entry_script.read_text(encoding="utf-8") == "test entry script"


@pytest.mark.parametrize("test_source_dir", ["tests"])
def test_warning_without_license_file(
    convert_command,
    project_dir_with_files,
    dummy_app_name,
    test_source_dir,
):
    """A single warning is raised if changelog file is present but not license file."""
    convert_command.logger.warning = mock.MagicMock()

    create_file(convert_command.base_path / "CHANGELOG", "")
    convert_command.migrate_necessary_files(
        project_dir_with_files,
        test_source_dir,
        dummy_app_name,
    )

    convert_command.logger.warning.assert_called_once_with(
        f"\nLicense file not found in '{convert_command.base_path}'. "
        "Briefcase will create a template 'LICENSE' file."
    )


@pytest.mark.parametrize("test_source_dir", ["tests"])
def test_file_is_copied_if_no_license_file_specified(
    convert_command,
    project_dir_with_files,
    dummy_app_name,
    test_source_dir,
):
    """A license file is copied if no license file is specified in pyproject.toml."""
    create_file(convert_command.base_path / "CHANGELOG", "")
    assert not (convert_command.base_path / "LICENSE").exists()
    convert_command.migrate_necessary_files(
        project_dir_with_files,
        test_source_dir,
        dummy_app_name,
    )
    assert (convert_command.base_path / "LICENSE").exists()


@pytest.mark.parametrize("test_source_dir", ["tests"])
def test_pep621_specified_license_filename(
    convert_command,
    project_dir_with_files,
    dummy_app_name,
    test_source_dir,
):
    """No license file is copied if a license file is specified in pyproject.toml."""
    convert_command.logger.warning = mock.MagicMock()
    license_name = "LICENSE.txt"
    create_file(convert_command.base_path / license_name, "")
    create_file(
        convert_command.base_path / "pyproject.toml",
        f'[project]\nlicense = {{ file = "{license_name}" }}',
    )
    create_file(convert_command.base_path / "CHANGELOG", "")
    convert_command.migrate_necessary_files(
        project_dir_with_files,
        test_source_dir,
        dummy_app_name,
    )
    assert not (convert_command.base_path / "LICENSE").exists()


@pytest.mark.parametrize("test_source_dir", ["tests"])
def test_pep621_specified_license_text(
    convert_command,
    project_dir_with_files,
    dummy_app_name,
    test_source_dir,
):
    """A license file is copied if the license is specified as text and no LICENSE file
    exists."""
    convert_command.logger.warning = mock.MagicMock()
    create_file(
        convert_command.base_path / "pyproject.toml",
        '[project]\nlicense = { text = "New BSD" }',
    )
    create_file(convert_command.base_path / "CHANGELOG", "")
    convert_command.migrate_necessary_files(
        project_dir_with_files,
        test_source_dir,
        dummy_app_name,
    )
    assert (convert_command.base_path / "LICENSE").exists()

    convert_command.logger.warning.assert_called_once_with(
        f"\nLicense file not found in '{convert_command.base_path}'. "
        "Briefcase will create a template 'LICENSE' file."
    )


@pytest.mark.parametrize("test_source_dir", ["tests"])
def test_warning_without_changelog_file(
    convert_command,
    project_dir_with_files,
    dummy_app_name,
    test_source_dir,
):
    """A single warning is raised if license file is present but not changelog file."""
    convert_command.logger.warning = mock.MagicMock()

    create_file(convert_command.base_path / "LICENSE", "")
    convert_command.migrate_necessary_files(
        project_dir_with_files,
        test_source_dir,
        dummy_app_name,
    )

    convert_command.logger.warning.assert_called_once_with(
        f"\nChangelog file not found in '{convert_command.base_path}'. You should either "
        f"create a new '{convert_command.base_path / 'CHANGELOG'}' file, or rename an "
        "already existing changelog file to 'CHANGELOG'."
    )


@pytest.mark.parametrize("test_source_dir", ["tests"])
def test_no_warning_with_license_and_changelog_file(
    convert_command,
    project_dir_with_files,
    dummy_app_name,
    test_source_dir,
):
    """No warning is raised if both license file and changelog file is present."""
    convert_command.logger.warning = mock.MagicMock()

    create_file(
        convert_command.base_path / "pyproject.toml",
        '[project]\nlicense = { file = "LICENSE.txt" }',
    )
    create_file(convert_command.base_path / "LICENSE.txt", "")
    create_file(convert_command.base_path / "CHANGELOG", "")
    convert_command.migrate_necessary_files(
        project_dir_with_files,
        test_source_dir,
        dummy_app_name,
    )

    convert_command.logger.warning.assert_not_called()


@pytest.mark.parametrize("test_source_dir", ["tests"])
def test_two_warnings_without_license_and_changelog_file(
    convert_command,
    project_dir_with_files,
    dummy_app_name,
    test_source_dir,
):
    """Two warnings are raised if both license file and changelog file are missing."""
    convert_command.logger.warning = mock.MagicMock()

    convert_command.migrate_necessary_files(
        project_dir_with_files,
        test_source_dir,
        dummy_app_name,
    )
    license_warning = (
        f"\nLicense file not found in '{convert_command.base_path}'. "
        "Briefcase will create a template 'LICENSE' file."
    )
    changelog_warning = (
        f"\nChangelog file not found in '{convert_command.base_path}'. You should either "
        f"create a new '{convert_command.base_path / 'CHANGELOG'}' file, or rename an "
        "already existing changelog file to 'CHANGELOG'."
    )
    assert convert_command.logger.warning.mock_calls == [
        mock.call(license_warning),
        mock.call(changelog_warning),
    ]
