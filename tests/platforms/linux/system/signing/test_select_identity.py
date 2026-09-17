import pytest

from briefcase.exceptions import BriefcaseCommandError

from .conftest import BOB, JANE


def test_select_identity_by_fingerprint(package_command, mock_gpg):
    """An identity can be selected by full fingerprint."""
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }

    result = package_command.select_identity(JANE)

    assert result == JANE
    # User input was not solicited
    assert package_command.console.prompts == []


def test_select_identity_by_key_id(package_command, mock_gpg):
    """An identity can be selected by key ID (a substring of the fingerprint)."""
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }

    result = package_command.select_identity("F9FCBC4A7701B685")

    assert result == JANE
    # User input was not solicited
    assert package_command.console.prompts == []


def test_select_identity_by_name(package_command, mock_gpg):
    """An identity can be selected by name or email address."""
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }

    result = package_command.select_identity("jane@example.com")

    assert result == JANE
    # User input was not solicited
    assert package_command.console.prompts == []


def test_select_identity_invalid(package_command, mock_gpg):
    """An identity that can't be found raises an error."""
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Invalid signing identity not-an-identity",
    ):
        package_command.select_identity("not-an-identity")

    # User input was not solicited
    assert package_command.console.prompts == []


def test_select_identity_no_identities(package_command, mock_gpg):
    """If no identities are available, the user is offered only "Don't sign"."""
    package_command.console.values = [""]

    result = package_command.select_identity()

    assert result is None
    # The user was prompted, and "Don't sign" was the default selection
    assert package_command.console.prompts == ["GPG signing identity [1]: "]


def test_select_identity_single(package_command, mock_gpg):
    """If only one identity is available, it is the default selection."""
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
    }
    package_command.console.values = [""]

    result = package_command.select_identity()

    assert result == JANE
    # The user was prompted, and the single identity was the default selection
    assert package_command.console.prompts == ["GPG signing identity [2]: "]


def test_select_identity_multiple(package_command, mock_gpg):
    """If multiple identities are available, the user is prompted to select one."""
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }

    # Select option 2 (option 1 is "Don't sign")
    package_command.console.values = ["2"]

    result = package_command.select_identity()

    assert result == JANE
    # User input was solicited once
    assert package_command.console.prompts == ["GPG signing identity: "]


def test_select_identity_dont_sign(package_command, mock_gpg):
    """The user can opt out of signing from the menu."""
    mock_gpg.identities.return_value = {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }

    # Select option 1 ("Don't sign")
    package_command.console.values = ["1"]

    result = package_command.select_identity()

    assert result is None
    # User input was solicited once
    assert package_command.console.prompts == ["GPG signing identity: "]
