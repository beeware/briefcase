from unittest.mock import MagicMock

from ...utils import PartialMatchString


def test_pep621_author(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    mock_input_text.return_value = "Some Name"
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)
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
    mock_input_text.assert_called_once_with(
        intro=PartialMatchString("the selected author name"),
        variable="author's email",
        default="mail3@tld.com",
        validator=convert_command.validate_email,
        override_value=None,
    )


def test_pep621_wrong_author(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    mock_input_text.return_value = "Some Name"
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)
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
    mock_input_text.assert_called_once_with(
        intro=PartialMatchString("the author name and bundle"),
        variable="author's email",
        default="noname@bundle.some",
        validator=convert_command.validate_email,
        override_value=None,
    )


def test_no_pep621_author(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    mock_input_text.return_value = "Some Name"
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    convert_command.input_email("Noname Thirdauthor", "some.bundle", None)
    mock_input_text.assert_called_once_with(
        intro=PartialMatchString("the author name and bundle"),
        variable="author's email",
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
    convert_command.input.values = ["my@email.com"]
    assert (
        convert_command.input_email("Some name", "com.some.bundle", None)
        == "my@email.com"
    )
