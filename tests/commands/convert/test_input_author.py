from unittest.mock import MagicMock

import pytest

from ...utils import NoMatchString, PartialMatchString


def test_multiple_pep621_authors(convert_command, monkeypatch):
    """All authors are added to the options in addition to an option for Other."""
    mock_select_option = MagicMock()
    mock_select_option.return_value = "Firstname Firstauthor"
    monkeypatch.setattr(convert_command, "select_option", mock_select_option)

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

    mock_select_option.assert_called_once_with(
        intro=PartialMatchString(
            "We found these author names in the PEP621 formatted 'pyproject.toml'."
        ),
        variable="Author",
        options=[
            "Firstname Firstauthor",
            "Name Thirdauthor",
            "Firstname Fourthauthor",
            "Firstname Firstauthor, Name Thirdauthor & Firstname Fourthauthor",
            "Other",
        ],
        default=None,
        override_value=None,
    )


def test_single_pep621_author(convert_command, monkeypatch):
    """If there is only one author, then you don't get the joined authors-option."""
    mock_select_option = MagicMock()
    mock_select_option.return_value = "Firstname Firstauthor"
    monkeypatch.setattr(convert_command, "select_option", mock_select_option)

    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n"
        "authors = [\n"
        '    {name="Firstname Firstauthor", email="mail1@tld.com"},\n'
        "]",
        encoding="utf-8",
    )
    convert_command.input_author(None)

    mock_select_option.assert_called_once_with(
        intro=PartialMatchString(
            "We found these author names in the PEP621 formatted 'pyproject.toml'."
        ),
        variable="Author",
        options=[
            "Firstname Firstauthor",
            "Other",
        ],
        default=None,
        override_value=None,
    )


def test_multiple_pep621_authors_select_other(convert_command, monkeypatch):
    """If you select "Other", then you can type in a name."""
    mock_select_option = MagicMock()
    mock_select_option.return_value = "Other"
    monkeypatch.setattr(convert_command, "select_option", mock_select_option)
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
    assert convert_command.input_author(None) == "Some Name"
    mock_select_option.assert_called_once_with(
        intro=PartialMatchString(
            "We found these author names in the PEP621 formatted 'pyproject.toml'."
        ),
        variable="Author",
        options=[
            "Firstname Firstauthor",
            "Name Thirdauthor",
            "Firstname Fourthauthor",
            "Firstname Firstauthor, Name Thirdauthor & Firstname Fourthauthor",
            "Other",
        ],
        default=None,
        override_value=None,
    )
    mock_input_text.assert_called_once_with(
        intro="Who do you want to be credited as the author of this application?",
        variable="author",
        default="Jane Developer",
        override_value=None,
    )


@pytest.mark.parametrize("write_empty_pyproject", [True, False])
def test_no_pep621_author(convert_command, monkeypatch, write_empty_pyproject):
    """If there is no author names in the pyproject.toml, then you're asked to write the
    name."""
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    if write_empty_pyproject:
        (convert_command.base_path / "pyproject.toml").write_text(
            "[project]\n" "authors = [\n" '    {email="mail1@tld.com"},\n' "]",
            encoding="utf-8",
        )
    convert_command.input_author(None)
    mock_input_text.assert_called_once_with(
        intro=NoMatchString(
            "We found these author names in the PEP621 formatted pyproject.toml."
        ),
        variable="author",
        default="Jane Developer",
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
    assert convert_command.input_author("Some Developer") == "Some Developer"


def test_prompted_author_without_pyproject(convert_command):
    """The user is prompted for an author."""
    convert_command.input.values = ["Some author"]
    assert convert_command.input_author(None) == "Some author"


def test_prompted_author_with_pyproject(convert_command):
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
    convert_command.input.values = ["2"]
    assert convert_command.input_author(None) == "Name Thirdauthor"


def test_prompted_author_with_pyproject_joined_author(convert_command):
    """You can select all authors joined together."""
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
    convert_command.input.values = ["4"]
    assert (
        convert_command.input_author(None)
        == "Firstname Firstauthor, Name Thirdauthor & Firstname Fourthauthor"
    )


def test_prompted_author_with_pyproject_other(convert_command):
    """If you select "Other", then you can type in a name."""
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
    convert_command.input.values = ["5", "Some Author"]
    assert convert_command.input_author(None) == "Some Author"
