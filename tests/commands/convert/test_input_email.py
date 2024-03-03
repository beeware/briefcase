from unittest.mock import MagicMock


def test_pep621_author(convert_command, monkeypatch):
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

    convert_command.input_email("Name Thirdauthor", "some.bundle", None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "mail3@tld.com"
    assert "the selected author name" in m_input_text.call_args.kwargs["intro"]


def test_pep621_wrong_author(convert_command, monkeypatch):
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

    convert_command.input_email("Noname Thirdauthor", "some.bundle", None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "noname@bundle.some"
    assert "the author name and bundle" in m_input_text.call_args.kwargs["intro"]


def test_no_pep621_author(convert_command, monkeypatch):
    m_input_text = MagicMock()
    m_input_text.return_value = "Some Name"
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    convert_command.input_email("Noname Thirdauthor", "some.bundle", None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "noname@bundle.some"
    assert "the author name and bundle" in m_input_text.call_args.kwargs["intro"]


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
    assert (
        convert_command.input_email(
            "Noname Thirdauthor", "some.bundle", "some@email.com"
        )
        == "some@email.com"
    )
