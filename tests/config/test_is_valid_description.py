import pytest

from briefcase.config import is_valid_description


@pytest.mark.parametrize(
    "description",
    [
        "a short valid description",
        "anoutherValidDescription42",
        "A description with spaces",
        "a mid size description with-hyphens and_underscores",
        "a" * 80,
    ],
)
def test_is_valid_description(description):
    """Test that valid descriptions are accepted."""
    assert is_valid_description(description)


@pytest.mark.parametrize(
    "description",
    [
        "a long description that should be rejected because it is way too long and goes over the char limit",
        "a" * 81,
    ],
)
def test_is_invalid_description(description):
    """Test that invalid descriptions are rejected."""
    assert not is_valid_description(description)
