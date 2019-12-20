import pytest


@pytest.mark.parametrize(
    'email',
    [
        'foo@example.com',
    ]
)
def test_valid_email(new_command, email):
    "Test that valid email addresses are accepted"
    assert new_command.is_valid_email(email)


@pytest.mark.parametrize(
    'email',
    [
        'not a email address!',  # Free text.
    ]
)
def test_invalid_email(new_command, email):
    "Test that invalid email addresses are rejected"
    with pytest.raises(ValueError):
        new_command.is_valid_email(email)
