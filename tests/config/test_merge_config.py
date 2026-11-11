from unittest.mock import Mock, call

import pytest

from briefcase.config import BaseConfig, merge_config, normalize_config
from briefcase.exceptions import BriefcaseConfigError


def test_merge_no_options_no_data():
    """If there are no initial options or new additional options, nothing changes."""
    config = {"other": 1234}

    merge_config(config, {})

    assert config == {"other": 1234}


def test_merge_no_data():
    """If there are no new options, nothing changes."""
    config = {
        "requires": ["first", "second"],
        "permission": {"up": True, "down": False},
        "other": 1234,
    }

    merge_config(config, {})

    assert config == {
        "requires": ["first", "second"],
        "permission": {"up": True, "down": False},
        "other": 1234,
    }


def test_merge_no_option():
    """If there are no existing options, the new option become the entire value."""
    config = {"other": 1234}

    merge_config(
        config,
        {
            "requires": ["third", "fourth"],
            "permission": {"left": True, "right": False},
        },
    )

    assert config == {
        "requires": ["third", "fourth"],
        "permission": {"left": True, "right": False},
        "other": 1234,
    }


def test_merge():
    """If there are existing options and new options, merge."""
    config = {
        "requires": ["first", "second"],
        "permission": {"up": True, "down": False},
        "other": 1234,
    }

    merge_config(
        config,
        {
            "requires": ["third", "fourth"],
            "permission": {"left": True, "right": False},
            "other": 5678,
        },
    )

    assert config == {
        "requires": ["first", "second", "third", "fourth"],
        "permission": {"up": True, "down": False, "left": True, "right": False},
        "other": 5678,
    }


def test_merge_collision():
    """If there are repeated options, lists are appended, dictionaries are updated and
    new options, merge."""
    config = {
        "requires": ["first", "second"],
        "permission": {"up": True, "down": False},
        "other": 1234,
    }

    merge_config(
        config,
        {
            "requires": ["second", "fourth"],
            "permission": {"down": True, "right": False},
            "other": 5678,
        },
    )

    assert config == {
        "requires": ["first", "second", "second", "fourth"],
        "permission": {"up": True, "down": True, "right": False},
        "other": 5678,
    }


def test_convert_base_definition():
    """The merge operation succeeds when called on itself."""
    config = {
        "requires": ["first", "second"],
        "permission": {"up": True, "down": False},
        "other": 1234,
    }

    merge_config(config, config)

    assert config == {
        "requires": ["first", "second"],
        "permission": {"up": True, "down": False},
        "other": 1234,
    }


def test_merged_keys():
    """There are multiple mergeable keys."""
    config = {
        "requires": ["first", "second"],
        "sources": ["a", "b"],
        "permission": {"up": True, "down": False},
        "non-merge": ["1", "2"],
        "other": 1234,
    }

    merge_config(
        config,
        {
            "requires": ["third", "fourth"],
            "permission": {"left": True, "right": False},
            "sources": ["c", "d"],
            "non-merge": ["3", "4"],
        },
    )

    assert config == {
        "requires": ["first", "second", "third", "fourth"],
        "sources": ["a", "b", "c", "d"],
        "permission": {"up": True, "down": False, "left": True, "right": False},
        "non_merge": ["3", "4"],
        "other": 1234,
    }


def test_merge_hyphenated_settings():
    """Hyphenated setting names are normalized to underscore form."""
    config = {
        "test_requires": ["first"],
        "formal_name": "Old Name",
    }

    console = Mock()
    merge_config(
        config,
        {
            "test-requires": ["second"],
            "formal-name": "New Name",
            "cleanup-paths": ["build"],
        },
        console=console,
    )

    assert config == {
        "test_requires": ["first", "second"],
        "formal_name": "New Name",
        "cleanup_paths": ["build"],
    }
    console.warning.assert_not_called()


def test_merge_underscore_warning():
    """Underscore setting names trigger a deprecation warning."""
    config = {}
    console = Mock()

    merge_config(
        config,
        {
            "test_requires": ["pytest"],
            "formal_name": "My App",
        },
        console=console,
    )

    assert config == {
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


def test_merge_conflicting_settings():
    """Specifying both hyphen and underscore forms of a setting raises an error."""
    config = {}
    console = Mock()

    with pytest.raises(
        BriefcaseConfigError,
        match=(
            r"Configuration specifies both 'test-requires' and 'test_requires'; "
            r"use 'test-requires'\."
        ),
    ):
        merge_config(
            config,
            {
                "test-requires": ["pytest"],
                "test_requires": ["unittest"],
            },
            console=console,
        )


def test_merge_conflicting_settings_reverse_order():
    """Specifying both forms raises an error regardless of key evaluation order."""
    config = {}

    with pytest.raises(
        BriefcaseConfigError,
        match=(
            r"Configuration specifies both 'formal-name' and 'formal_name'; "
            r"use 'formal-name'\."
        ),
    ):
        merge_config(
            config,
            {
                "formal_name": "App A",
                "formal-name": "App B",
            },
        )


def test_merge_into_base_config_instance():
    """Merging into a BaseConfig instance normalizes hyphenated keys into attributes."""
    config = BaseConfig(formal_name="Old", test_requires=["a"])
    console = Mock()

    merge_config(
        config,
        {
            "formal-name": "New",
            "test-requires": ["b"],
        },
        console=console,
    )

    assert config.formal_name == "New"
    assert config.test_requires == ["a", "b"]
    console.warning.assert_not_called()


def test_normalize_config_idempotent():
    """Multiple normalize_config calls with shared normalized set only warn once."""
    data = {"formal_name": "My App"}
    console = Mock()
    normalized = set()

    normalize_config(data, console=console, normalized=normalized)
    assert console.warning.call_count == 1

    # Second call does not warn again
    normalize_config(data, console=console, normalized=normalized)
    assert console.warning.call_count == 1
    assert data["formal_name"] == "My App"
