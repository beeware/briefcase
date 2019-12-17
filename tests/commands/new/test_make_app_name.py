import pytest


@pytest.mark.parametrize(
    'formal_name, candidate',
    [
        ('Hello World', 'helloworld'),
        ('Hello World!', 'helloworld'),
        ('Hello! World', 'helloworld'),
        ('Hello-World', 'helloworld'),
    ]
)
def test_make_app_name(new_command, formal_name, candidate):
    "A formal name can be converted into a valid app name."
    app_name = new_command.make_app_name(formal_name)
    assert app_name == candidate
    # Double check - the app name passes the validity check.
    assert new_command.is_valid_app_name(app_name)
