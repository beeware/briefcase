import pytest

from briefcase.config import is_reserved_keyword


@pytest.mark.parametrize(
    "name",
    [
        # These names may not be valid identifiers,
        # but they're not reserved words in any language we care about.
        "BLACK",
        "purple",
        "9pink",
        "Yellow",
        "green",
        "hello world",
    ],
)
def test_is_not_reserved_keyword_violation(name):
    """Test that names not in the keywords list return false."""
    assert not is_reserved_keyword(name)


@pytest.mark.parametrize(
    "name",
    [
        # Python specific keyword, in various case variants
        "pass",
        "Pass",
        "PASS",
        # Javascript specific keyword, in various case variants
        "in",
        "In",
        "IN",
        # Java specific keyword, in various case variants
        "synchronized",
        "Synchronized",
        "SYNCHRONIZED",
        # Keyword in multiple languages, in various case variants
        "false",
        "False",
        "FALSE",
        # Windows reserved keywords
        "CON",
        "con",  # lower case version of reserved name
        "LPT5",
        "Lpt5",  # unconventional spelling of reserved name
    ],
)
def test_is_reserved_keyword(name):
    """Test that names in the reserved_keywords list returns true."""
    assert is_reserved_keyword(name)
