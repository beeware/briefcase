from unittest.mock import MagicMock


def test_no_test_dir(convert_command, monkeypatch):
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    convert_command.input_test_source_dir("app_name", None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "tests"

    info_content = "\n\nBased on your project's folder structure, we believe 'test' might be your test directory"
    assert info_content not in m_input_text.call_args.kwargs["intro"]


def test_test_dir(convert_command, monkeypatch):
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    (convert_command.base_path / "test").mkdir()
    convert_command.input_test_source_dir("app_name", None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "test"

    info_content = "\n\nBased on your project's folder structure, we believe 'test' might be your test directory"
    assert info_content in m_input_text.call_args.kwargs["intro"]


def test_tests_dir(convert_command, monkeypatch):
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    (convert_command.base_path / "tests").mkdir()
    convert_command.input_test_source_dir("app_name", None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "tests"

    info_content = "\n\nBased on your project's folder structure, we believe 'tests' might be your test directory"
    assert info_content in m_input_text.call_args.kwargs["intro"]


def test_override_is_used(convert_command):
    (convert_command.base_path / "test_dir").mkdir()
    assert convert_command.input_test_source_dir("app_name", "test_dir") == "test_dir"
