import pytest

from briefcase.config import is_reserved_keyword_violation


@pytest.mark.parametrize(
    'name',
    [
        'BLACK',
        'purple',
        '9pink',
        'Yellow',
        'green',
    ]
)
def test_is_not_reserved_keyword_violation(name):
    "Test that names not in the keywords list return false."
    assert is_reserved_keyword_violation(name) == False


@pytest.mark.parametrize(
    'name',
    [
        'abstract',
        'break',
        'byte',
        'case',
        'catch',
        'pass',
        'false',
        'False',
        'YIELD',
    ]
)

def test_is_reserved_keyword_violation(name):
     "Test that names in the reserved_keywords list returns true"
     assert is_reserved_keyword_violation(name) == True

