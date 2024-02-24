from unittest.mock import MagicMock

import pytest


def test_multiple_pep621_authors(convert_command, monkeypatch):
    """All authors are added to the options in addition to an option for Other."""
    m_select_option = MagicMock()
    m_select_option.return_value = "Firstname Firstauthor"
    monkeypatch.setattr(convert_command, "select_option", m_select_option)

    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n"
        "authors = [\n"
        '    {name="Firstname Firstauthor", email="mail1@tld.com"},\n'
        '    {email="mail2@tld.com"},\n'
        '    {name="Name Thirdauthor", email="mail3@tld.com"},\n'
        '    {name="Firstname Fourthauthor", email="mail4@tld.com"},\n'
        "]",
        encoding="utf-8",
    )
    convert_command.input_author(None)
    m_select_option.assert_called_once()
    assert m_select_option.call_args.kwargs["options"] == [
        "Firstname Firstauthor",
        "Name Thirdauthor",
        "Firstname Fourthauthor",
        "Firstname Firstauthor, Name Thirdauthor & Firstname Fourthauthor",
        "Other",
    ]


def test_multiple_pep621_authors_select_other(convert_command, monkeypatch):
    """If you select "Other", then you can type in a name."""
    m_select_option = MagicMock()
    m_select_option.return_value = "Other"
    monkeypatch.setattr(convert_command, "select_option", m_select_option)
    m_input_text = MagicMock()
    m_input_text.return_value = "Some Name"
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n"
        "authors = [\n"
        '    {name="Firstname Firstauthor", email="mail1@tld.com"},\n'
        '    {email="mail2@tld.com"},\n'
        '    {name="Name Thirdauthor", email="mail3@tld.com"},\n'
        '    {name="Firstname Fourthauthor", email="mail4@tld.com"},\n'
        "]",
        encoding="utf-8",
    )
    assert convert_command.input_author(None) == "Some Name"
    m_select_option.assert_called_once()
    m_input_text.assert_called_once()


def test_single_pep621_author(convert_command, monkeypatch):
    """If there is only one author, then you don't get the option select prompt."""
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n"
        "authors = [\n"
        '    {name="Firstname Firstauthor", email="mail1@tld.com"},\n'
        "]",
        encoding="utf-8",
    )
    convert_command.input_author(None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "Firstname Firstauthor"


@pytest.mark.parametrize("write_empty_pyproject", [True, False])
def test_no_pep621_author(convert_command, monkeypatch, write_empty_pyproject):
    """If there is no author names in the pyproject.toml, then you're asked to write the
    name."""
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    if write_empty_pyproject:
        (convert_command.base_path / "pyproject.toml").write_text(
            "[project]\n" "authors = [\n" '    {email="mail1@tld.com"},\n' "]",
            encoding="utf-8",
        )
    convert_command.input_author(None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "Jane Developer"


def test_override(convert_command):
    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n"
        "authors = [\n"
        '    {name="Firstname Firstauthor", email="mail1@tld.com"},\n'
        '    {email="mail2@tld.com"},\n'
        '    {name="Name Thirdauthor", email="mail3@tld.com"},\n'
        '    {name="Firstname Fourthauthor", email="mail4@tld.com"},\n'
        "]",
        encoding="utf-8",
    )
    assert convert_command.input_author("Some Developer") == "Some Developer"
