import pytest

from briefcase.exceptions import CorruptContentError


def test_matching_hash(mock_tools, capsys):
    """If the expected and actual hash match, nothing is raised or logged."""
    mock_tools.file.check_hash(
        role="template 'https://example.com/thing.git'",
        expected_hash="sha1:abc123",
        actual_hash="sha1:ABC123",
    )

    assert capsys.readouterr().out == ""


def test_mismatch_raises_exception_cls(mock_tools):
    """If the hashes don't match, exception_cls is raised with the right args."""
    with pytest.raises(CorruptContentError) as exc_info:
        mock_tools.file.check_hash(
            role="template 'https://example.com/thing.git'",
            expected_hash="sha1:abc123",
            actual_hash="sha1:def456",
        )

    assert exc_info.value.role == "template 'https://example.com/thing.git'"
    assert exc_info.value.expected_hash == "sha1:abc123"
    assert exc_info.value.actual_hash == "sha1:def456"


def test_mismatched_label_is_a_mismatch(mock_tools):
    """A matching digest with a different label is still treated as a mismatch."""
    with pytest.raises(CorruptContentError) as exc_info:
        mock_tools.file.check_hash(
            role="template 'https://example.com/thing.git'",
            expected_hash="sha256:abc123",
            actual_hash="sha1:abc123",
        )

    assert exc_info.value.expected_hash == "sha256:abc123"
    assert exc_info.value.actual_hash == "sha1:abc123"


def test_no_hash_available_warns(mock_tools, capsys):
    """If expected_hash is None, a warning is logged and no comparison is made."""
    mock_tools.file.check_hash(
        role="template 'https://example.com/thing.git'",
        expected_hash=None,
        actual_hash="sha1:anything-at-all",
    )

    assert (
        "will not be verified as no reference hash has been provided"
        in capsys.readouterr().out
    )


def test_unverified_is_silent(mock_tools, capsys):
    """An 'unverified:<reason>' expected_hash skips verification without a warning."""
    mock_tools.file.check_hash(
        role="template 'https://example.com/thing.git'",
        expected_hash="unverified:this template has no stable hash",
        actual_hash="sha1:anything-at-all",
    )

    assert capsys.readouterr().out == ""
