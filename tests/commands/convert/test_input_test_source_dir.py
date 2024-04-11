from unittest.mock import ANY, MagicMock

from ...utils import NoMatchString, PartialMatchString


def test_no_test_dir(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    convert_command.input_test_source_dir("app_name", None)
    intro_content = "\n\nBased on your project's folder structure, we believe 'test' might be your test directory"
    mock_input_text.assert_called_once_with(
        intro=NoMatchString(intro_content),
        variable="test source directory",
        default="tests",
        validator=ANY,
        override_value=None,
    )


def test_test_dir(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    (convert_command.base_path / "test").mkdir()
    convert_command.input_test_source_dir("app_name", None)

    intro_content = "\n\nBased on your project's folder structure, we believe 'test' might be your test directory"
    mock_input_text.assert_called_once_with(
        intro=PartialMatchString(intro_content),
        variable="test source directory",
        default="test",
        validator=ANY,
        override_value=None,
    )


def test_tests_dir(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    (convert_command.base_path / "tests").mkdir()
    convert_command.input_test_source_dir("app_name", None)

    intro_content = "\n\nBased on your project's folder structure, we believe 'tests' might be your test directory"
    mock_input_text.assert_called_once_with(
        intro=PartialMatchString(intro_content),
        variable="test source directory",
        default="tests",
        validator=ANY,
        override_value=None,
    )


def test_tests_dir_is_prefered_over_test_dir(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    (convert_command.base_path / "tests").mkdir()
    (convert_command.base_path / "test").mkdir()
    convert_command.input_test_source_dir("app_name", None)

    intro_content = "\n\nBased on your project's folder structure, we believe 'tests' might be your test directory"
    mock_input_text.assert_called_once_with(
        intro=PartialMatchString(intro_content),
        variable="test source directory",
        default="tests",
        validator=ANY,
        override_value=None,
    )


def test_override_is_used(convert_command):
    (convert_command.base_path / "test_dir").mkdir()
    assert convert_command.input_test_source_dir("app_name", "test_dir") == "test_dir"


def test_prompted_test_source_dir(convert_command):
    """You can type in the test source dir."""
    (convert_command.base_path / "mytest").mkdir(parents=True)
    convert_command.input.values = ["mytest"]

    assert convert_command.input_test_source_dir("app_name", None) == "mytest"
