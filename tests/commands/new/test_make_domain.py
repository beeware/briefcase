import pytest


@pytest.mark.parametrize(
    'bundle, candidate',
    [
        ('com.example', 'example.com'),
        ('com.example.more', 'more.example.com'),
    ]
)
def test_make_app_name(new_command, bundle, candidate):
    "A bundle can be converted into a domain name."
    app_name = new_command.make_domain(bundle)
    assert app_name == candidate
