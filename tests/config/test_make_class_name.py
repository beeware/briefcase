import keyword

import pytest

from briefcase.config import derive_class_name, make_class_name


@pytest.mark.parametrize(
    ("formal_name", "candidate"),
    [
        # Some simple cases
        ("Hello World", "HelloWorld"),
        ("Hello World!", "HelloWorld"),
        ("Hello! World", "HelloWorld"),
        ("Hello_World", "Hello_World"),
        ("Hello-World", "HelloWorld"),
        # Starting with a number
        ("24 Jump Street", "_24JumpStreet"),  # Unicode category Nd
        # Starting with an underscore
        ("_Hello_World", "_Hello_World"),
        # Unicode names
        ("你好 世界", "你好世界"),
        ("Hallo Vögel", "HalloVögel"),
        ("Bonjour Garçon", "BonjourGarçon"),
        # Unicode codepoints that can be at the start of an identifier
        ("\u02ec World", "\u02ecWorld"),  # Unicode category Lm
        ("\u3006 World", "\u3006World"),  # Unicode category Lo
        ("\u3021 World", "\u3021World"),  # Unicode category Nl
        # ('\u2118 World', '\u2118World'),  # in Other_ID_Start
        # Unicode codepoints that cannot be at the start of an identifier
        ("\u20e1 World", "_\u20e1World"),  # Unicode Category Mn
        ("\u0903 World", "_\u0903World"),  # Unicode Category Mc
        ("\u2040 World", "_\u2040World"),  # Category Pc
        # ('\u00B7 World', '_\u00B7World'),  # in Other_ID_Continue
        # Characters that are converted by NFKC normalization
        ("\u2135 World", "\u05d0World"),  # Unicode category Lo
        # Names that reduce to a Python keyword; `class lambda(...)` does not parse
        ("lambda", "_lambda"),
        ("None", "_None"),
        ("class", "_class"),
        # Soft keywords are legal class names, and case matters
        ("match", "match"),
        ("Lambda", "Lambda"),
        # Nothing identifier-like survives, so a generic name is used
        ("!!!", "Briefcase"),
        ("...", "Briefcase"),
        ("\U0001f389", "Briefcase"),
        ("", "Briefcase"),
    ],
)
def test_make_class_name(formal_name, candidate):
    """A formal name can be converted into a valid class name."""
    class_name = make_class_name(formal_name)
    assert class_name == candidate


@pytest.mark.parametrize(
    ("formal_name", "candidate"),
    [
        ("Hello World", "HelloWorld"),
        ("lambda", "_lambda"),
        # derive_class_name reports the empty result that make_class_name
        # replaces; validate_formal_name depends on being able to see it.
        ("!!!", ""),
        ("\U0001f389", ""),
        ("", ""),
    ],
)
def test_derive_class_name(formal_name, candidate):
    """The raw derivation is visible without the generic fallback."""
    assert derive_class_name(formal_name) == candidate


def test_make_class_name_is_always_an_identifier():
    """Whatever the formal name, the class name can be used in a class statement."""
    for formal_name in ["!!!", "...", "\U0001f389", "", "   ", "My App", "lambda"]:
        class_name = make_class_name(formal_name)
        assert class_name.isidentifier()
        assert not keyword.iskeyword(class_name)
