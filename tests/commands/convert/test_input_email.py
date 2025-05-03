from unittest.mock import MagicMock

from ...utils import PartialMatchString


def test_pep621_author(convert_command, monkeypatch):
    mock_text_question = MagicMock()
    mock_text_question.return_value = "Some Name"
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)
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
    mock_text_question.assert_called_once_with(
        intro=PartialMatchString("the selected author name"),
        description="Author's Email",
        default="mail3@tld.com",
        validator=convert_command.validate_email,
        override_value=None,
    )


def test_pep621_wrong_author(convert_command, monkeypatch):
    mock_text_question = MagicMock()
    mock_text_question.return_value = "Some Name"
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)
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
    mock_text_question.assert_called_once_with(
        intro=PartialMatchString("the author name and bundle"),
        description="Author's Email",
        default="noname@bundle.some",
        validator=convert_command.validate_email,
        override_value=None,
    )


def test_no_pep621_author(convert_command, monkeypatch):
    mock_text_question = MagicMock()
    mock_text_question.return_value = "Some Name"
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)

    convert_command.input_email("Noname Thirdauthor", "some.bundle", None)
    mock_text_question.assert_called_once_with(
        intro=PartialMatchString("the author name and bundle"),
        description="Author's Email",
        default="noname@bundle.some",
        validator=convert_command.validate_email,
        override_value=None,
    )


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


def test_prompted_email(convert_command):
    """You can type in the e-mail address."""
    convert_command.console.values = ["my@email.com"]
    assert (
        convert_command.input_email("Some name", "com.some.bundle", None)
        == "my@email.com"
    )


def test_default_email_from_git_config(convert_command, monkeypatch, capsys):
    """If git integration is configured, and a config value 'user.email' is available,
    use that value as default."""
    convert_command.tools.git = object()
    convert_command.get_git_config_value = MagicMock(return_value="my@email.com")
    convert_command.console.values = [""]

    assert (
        convert_command.input_email("Some name", "com.some.bundle", None)
        == "my@email.com"
    )
    convert_command.get_git_config_value.assert_called_once_with("user", "email")

    # RichConsole wraps long lines, so we have to unwrap before we check
    stdout = capsys.readouterr().out.replace("\n", " ")
    assert stdout == PartialMatchString("Based on your git configuration")
