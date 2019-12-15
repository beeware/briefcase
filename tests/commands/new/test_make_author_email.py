import pytest


@pytest.mark.parametrize(
    'name, bundle, candidate',
    [
        ('Jane Developer', 'com.example', 'jane@example.com'),
        ('Jane Developer', 'com.example.more', 'jane@more.example.com'),
        ('Jane', 'com.example', 'jane@example.com'),
    ]
)
def test_make_author_email(new_command, name, bundle, candidate):
    "An author name and bundle can be converted into a valid email address."
    email = new_command.make_author_email(name, bundle)
    assert email == candidate
    # Double check - the app name passes the validity check.
    assert new_command.is_valid_email(email)
