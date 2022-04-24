import pytest

from briefcase.console import Console


@pytest.mark.parametrize(
    'raw, converted',
    [
        ('Hello', 'Hello'),
        ('hello', 'Hello'),
        ('hello world', 'Hello World'),
        ("hello world's fair", "Hello World's Fair"),
        ("world of wonder", "World of Wonder"),
        ("hunt the wumpus", "Hunt the Wumpus"),
        ("scott pilgrim vs the world", "Scott Pilgrim vs the World"),

        # Specific examples that we know are problematic
        ("author's email", "Author's Email"),
        ("project URL", "Project URL"),
    ]
)
def test_titlecase(raw, converted):
    "Test that a string can be capitalized"
    assert Console.titlecase(raw) == converted
