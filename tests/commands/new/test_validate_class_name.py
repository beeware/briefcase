import pytest


@pytest.mark.parametrize(
    'name',
    [
        'HelloWorld',
        'HelloWorld98',
        'Hello42World',
        'Hello_World',
    ]
)
def test_valid_class_name(new_command, name):
    "Test that valid app names are accepted"
    assert new_command.validate_class_name(name)


@pytest.mark.parametrize(
    'name',
    [
        'hello world',  # space
        'helloworld!',  # punctuation
        '_helloworld',  # leading underscore
        '-helloworld',  # leading hyphen
        '98helloworld',  # leading digit
        '',  # blank
        '学口算',  # non-latin character
        'helloworld',  # no capitalized letter
    ]
)
def test_invalid_class_name(new_command, name, tmp_path):
    "Test that invalid app names are rejected"
    (tmp_path / 'existing').mkdir()

    with pytest.raises(ValueError):
        new_command.validate_class_name(name)
