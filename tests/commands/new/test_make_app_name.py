import pytest


@pytest.mark.parametrize(
    'formal_name, candidate',
    [
        ('Hello World', 'helloworld'),
        ('Hello World!', 'helloworld'),
        ('Hello! World', 'helloworld'),
        ('Hello-World', 'helloworld'),
        ('98 Hello World', 'helloworld'),
        ('Hello World_', 'helloworld'),
        ('Hello world.', 'helloworld'),
        ('_HelloWorld_', 'helloworld'),
        ('Hello_World_', 'hello_world'),
        ('Hello World-', 'helloworld'),
    ]
)
def test_make_app_name(new_command, formal_name, candidate):
    "A formal name can be converted into a valid app name."
    app_name = new_command.make_app_name(formal_name)
    assert app_name == candidate
    # Double check - the app name passes the validity check.
    assert new_command.validate_app_name(app_name)
