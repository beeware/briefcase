import pytest


@pytest.mark.parametrize(
    'name',
    [
        'helloworld',
        'helloWorld',
        'hello42world',
        'hello_world',
        'hello-world',
    ]
)
def test_valid_app_name(new_command, name):
    "Test that valid app names are accepted"
    assert new_command.validate_app_name(name)


@pytest.mark.parametrize(
    'name',
    [
        'hello world',  # space
        'helloworld!',  # punctuation
        '_helloworld',  # leading underscore
        '-helloworld',  # leading hyphen
        'existing',  # pre-existing directory
        '98helloworld',  # leading digit
        '',  # blank
        '学口算',  # non-latin character
        'Helloworld'  # start with capital letter
    ]
)
def test_invalid_app_name(new_command, name, tmp_path):
    "Test that invalid app names are rejected"
    (tmp_path / 'existing').mkdir()

    with pytest.raises(ValueError):
        new_command.validate_app_name(name)
