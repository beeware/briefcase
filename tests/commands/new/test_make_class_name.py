import pytest


@pytest.mark.parametrize(
    'formal_name, candidate',
    [
        ('Hello World', 'HelloWorld'),
        ('Hello World!', 'HelloWorld'),
        ('Hello! World', 'HelloWorld'),
        ('Hello_World', 'Hello_World'),
        ('Hello-World', 'HelloWorld'),
        ('24 Jump Street', 'JumpStreet'),
        ('hello world', 'HelloWorld')
    ]
)
def test_make_class_name(new_command, formal_name, candidate):
    "A formal name can be converted into a valid class name."
    class_name = new_command.make_class_name(formal_name)
    assert class_name == candidate
