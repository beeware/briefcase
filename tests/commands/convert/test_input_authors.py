from unittest.mock import MagicMock


def test_pep621_authors_are_used(convert_command):
    """If the pyproject.toml defines authors, they are used without prompting."""
    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n"
        "authors = [\n"
        '    {name="Firstname Firstauthor", email="mail1@tld.com"},\n'
        '    {name="Name Secondauthor", email="mail2@tld.com"},\n'
        "]",
        encoding="utf-8",
    )
    convert_command.console.text_question = MagicMock()
    convert_command.console.selection_question = MagicMock()

    authors, declare_authors = convert_command.input_authors("com.example", {})

    assert authors == [
        {"name": "Firstname Firstauthor", "email": "mail1@tld.com"},
        {"name": "Name Secondauthor", "email": "mail2@tld.com"},
    ]
    # The PEP 621 definition is used as-is, so it isn't repeated in the
    # Briefcase configuration.
    assert declare_authors is False

    # The user isn't asked anything.
    convert_command.console.text_question.assert_not_called()
    convert_command.console.selection_question.assert_not_called()


def test_no_pep621_authors_prompts(convert_command, monkeypatch):
    """If the pyproject.toml has no authors, the author details are prompted for."""
    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\nname = 'awesome'", encoding="utf-8"
    )
    monkeypatch.setattr(
        convert_command,
        "input_author",
        MagicMock(return_value="Grace Hopper"),
    )
    monkeypatch.setattr(
        convert_command,
        "input_email",
        MagicMock(return_value="grace@hopper.org"),
    )

    authors, declare_authors = convert_command.input_authors("com.example", {})

    assert authors == [{"name": "Grace Hopper", "email": "grace@hopper.org"}]
    assert declare_authors is True


def test_overrides_bypass_pep621_authors(convert_command, monkeypatch):
    """An author override takes precedence over the PEP 621 authors."""
    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n"
        "authors = [\n"
        '    {name="Firstname Firstauthor", email="mail1@tld.com"},\n'
        "]",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        convert_command,
        "input_author",
        MagicMock(return_value="Grace Hopper"),
    )
    monkeypatch.setattr(
        convert_command,
        "input_email",
        MagicMock(return_value="grace@hopper.org"),
    )

    authors, declare_authors = convert_command.input_authors(
        "com.example", {"author": "Grace Hopper"}
    )

    assert authors == [{"name": "Grace Hopper", "email": "grace@hopper.org"}]
    assert declare_authors is True
