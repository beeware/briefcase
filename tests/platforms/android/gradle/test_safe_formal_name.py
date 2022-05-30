import pytest

from briefcase.platforms.android.gradle import safe_formal_name


@pytest.mark.parametrize(
    "formal_name, safe_name",
    [
        ("Hello World", "Hello World"),
        # The invalid list is all stripped
        ("Hello/World/", "HelloWorld"),
        ("Hello\\World", "HelloWorld"),
        ("Hello:World", "HelloWorld"),
        ("Hello<World", "HelloWorld"),
        ("Hello>World", "HelloWorld"),
        ('Hello "World"', "Hello World"),
        ("Hello World?", "Hello World"),
        ("Hello|World", "HelloWorld"),
        ("Hello World!", "Hello World"),
        # All invalid punctuation is removed
        # Valid punctuation is preserved
        ("Hello! (World?)", "Hello (World)"),
        # Position of punctuation doesn't matter
        ("Hello! World", "Hello World"),
        ("!Hello World", "Hello World"),
        # If removing punctuation leads to double spaces, reduce the double spaces
        ("Hello | World", "Hello World"),
        ("Hello World |", "Hello World"),
        ("| Hello World", "Hello World"),
    ],
)
def test_safe_formal_name(formal_name, safe_name):
    assert safe_formal_name(formal_name) == safe_name
