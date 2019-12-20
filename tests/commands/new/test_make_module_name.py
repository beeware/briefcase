import pytest


@pytest.mark.parametrize(
    'app_name, candidate',
    [
        ('helloworld', 'helloworld'),
        ('HelloWorld', 'HelloWorld'),
        ('hello-world', 'hello_world'),
        ('hello_world', 'hello_world'),
    ]
)
def test_make_module_name(new_command, app_name, candidate):
    "An app name can be converted into a valid class name."
    module_name = new_command.make_module_name(app_name)
    assert module_name == candidate
