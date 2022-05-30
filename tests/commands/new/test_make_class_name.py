import pytest


@pytest.mark.parametrize(
    "formal_name, candidate",
    [
        # Some simple cases
        ("Hello World", "HelloWorld"),
        ("Hello World!", "HelloWorld"),
        ("Hello! World", "HelloWorld"),
        ("Hello_World", "Hello_World"),
        ("Hello-World", "HelloWorld"),
        # Startint with a number
        ("24 Jump Street", "_24JumpStreet"),  # Unicode category Nd
        # Starting with an underscore
        ("Hello_World", "Hello_World"),
        ("_Hello_World", "_Hello_World"),
        # Unicode names
        ("你好 世界", "你好世界"),
        ("Hallo Vögel", "HalloVögel"),
        ("Bonjour Garçon", "BonjourGarçon"),
        # Unicode codepoints that can be at the start of an identifier
        ("\u02EC World", "\u02ECWorld"),  # Unicode category Lm
        ("\u3006 World", "\u3006World"),  # Unicode category Lo
        ("\u3021 World", "\u3021World"),  # Unicode category Nl
        # ('\u2118 World', '\u2118World'),  # in Other_ID_Start noqa
        # Unicode codepoints that cannot be at the start of an identifer
        ("\u20E1 World", "_\u20E1World"),  # Unicode Category Mn
        ("\u0903 World", "_\u0903World"),  # Unicode Category Mc
        ("\u2040 World", "_\u2040World"),  # Category Pc
        # ('\u00B7 World', '_\u00B7World'),  # in Other_ID_Continue noqa
        # Characters that are converted by NFKC normalization
        ("\u2135 World", "\u05d0World"),  # Unicode category Lo
    ],
)
def test_make_class_name(new_command, formal_name, candidate):
    """A formal name can be converted into a valid class name."""
    class_name = new_command.make_class_name(formal_name)
    assert class_name == candidate
