from unittest.mock import ANY, MagicMock

from ...utils import NoMatchString, PartialMatchString


def test_no_test_dir(convert_command, monkeypatch):
    mock_text_question = MagicMock()
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)

    convert_command.input_test_source_dir("app_name", None)
    intro_content = "\n\nBased on your project's folder structure, we believe 'test' might be your test directory"
    mock_text_question.assert_called_once_with(
        intro=NoMatchString(intro_content),
        description="Test Source Directory",
        default="tests",
        validator=ANY,
        override_value=None,
    )


def test_test_dir(convert_command, monkeypatch):
    mock_text_question = MagicMock()
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)

    (convert_command.base_path / "test").mkdir()
    convert_command.input_test_source_dir("app_name", None)

    intro_content = "\n\nBased on your project's folder structure, we believe 'test' might be your test directory"
    mock_text_question.assert_called_once_with(
        intro=PartialMatchString(intro_content),
        description="Test Source Directory",
        default="test",
        validator=ANY,
        override_value=None,
    )


def test_tests_dir(convert_command, monkeypatch):
    mock_text_question = MagicMock()
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)

    (convert_command.base_path / "tests").mkdir()
    convert_command.input_test_source_dir("app_name", None)

    intro_content = "\n\nBased on your project's folder structure, we believe 'tests' might be your test directory"
    mock_text_question.assert_called_once_with(
        intro=PartialMatchString(intro_content),
        description="Test Source Directory",
        default="tests",
        validator=ANY,
        override_value=None,
    )


def test_tests_dir_is_prefered_over_test_dir(convert_command, monkeypatch):
    mock_text_question = MagicMock()
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)

    (convert_command.base_path / "tests").mkdir()
    (convert_command.base_path / "test").mkdir()
    convert_command.input_test_source_dir("app_name", None)

    intro_content = "\n\nBased on your project's folder structure, we believe 'tests' might be your test directory"
    mock_text_question.assert_called_once_with(
        intro=PartialMatchString(intro_content),
        description="Test Source Directory",
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
    convert_command.console.values = ["mytest"]

    assert convert_command.input_test_source_dir("app_name", None) == "mytest"
