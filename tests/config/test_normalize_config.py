from unittest.mock import Mock, call

import pytest

from briefcase.config import normalize_config
from briefcase.exceptions import BriefcaseConfigError


def test_normalize_hyphenated_keys():
    """Hyphenated setting names are normalized to underscore form without warning."""
    data = {
        "test-requires": ["pytest"],
        "formal-name": "My App",
        "cleanup-paths": ["build"],
    }
    console = Mock()

    res = normalize_config(data, console=console)

    assert res == {
        "test_requires": ["pytest"],
        "formal_name": "My App",
        "cleanup_paths": ["build"],
    }
    assert res is data
    console.warning.assert_not_called()


def test_normalize_underscore_keys_warning():
    """Underscore setting names trigger a deprecation warning."""
    data = {
        "test_requires": ["pytest"],
        "formal_name": "My App",
    }
    console = Mock()

    res = normalize_config(data, console=console)

    assert res == {
        "test_requires": ["pytest"],
        "formal_name": "My App",
    }
    assert console.warning.call_count == 2
    console.warning.assert_has_calls(
        [
            call(
                "Configuration setting 'test_requires' is deprecated; "
                "use 'test-requires' instead."
            ),
            call(
                "Configuration setting 'formal_name' is deprecated; "
                "use 'formal-name' instead."
            ),
        ]
    )


def test_normalize_conflict_raises_error():
    """Specifying both hyphen and underscore forms of a setting raises an error."""
    data = {
        "test-requires": ["pytest"],
        "test_requires": ["unittest"],
    }
    console = Mock()

    with pytest.raises(
        BriefcaseConfigError,
        match=(
            r"Configuration specifies both 'test-requires' and 'test_requires'; "
            r"use 'test-requires'\."
        ),
    ):
        normalize_config(data, console=console)


def test_normalize_conflict_reverse_order():
    """Specifying both forms raises an error regardless of key evaluation order."""
    data = {
        "formal_name": "App A",
        "formal-name": "App B",
    }

    with pytest.raises(
        BriefcaseConfigError,
        match=(
            r"Configuration specifies both 'formal-name' and 'formal_name'; "
            r"use 'formal-name'\."
        ),
    ):
        normalize_config(data)


def test_normalize_without_console():
    """normalize_config can be called directly without passing a console."""
    data = {"formal-name": "My App", "version": "1.0.0"}
    res = normalize_config(data)
    assert res == {"formal_name": "My App", "version": "1.0.0"}


def test_normalize_unaffected_keys():
    """Keys without hyphens or underscores are left unchanged."""
    data = {
        "bundle": "com.example",
        "version": "1.0.0",
        "sources": ["src"],
    }
    console = Mock()
    res = normalize_config(data, console=console)
    assert res == {
        "bundle": "com.example",
        "version": "1.0.0",
        "sources": ["src"],
    }
    console.warning.assert_not_called()
