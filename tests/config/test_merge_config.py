import pytest

from briefcase.config import merge_config


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
        "non-merge": ["3", "4"],
        "other": 1234,
    }


def test_merge_hooks():
    """The hooks table is cumulative: a later layer adds or replaces stages."""
    config = {}
    merge_config(
        config,
        {"hooks": {"pre_build": [["echo", "app"]], "post_create": [["echo", "a"]]}},
    )
    merge_config(config, {"hooks": {"post_create": [["echo", "ios"]]}})

    assert config == {
        "hooks": {
            "pre_build": [["echo", "app"]],
            "post_create": [["echo", "ios"]],
        }
    }


@pytest.mark.parametrize(
    "hooks",
    [
        "echo done",  # a string
        [["ruby", "patch.rb", "--verbose"]],  # commands without a stage
    ],
)
def test_merge_hooks_not_a_table(hooks):
    """A hooks value that isn't a table is kept as given, for validation to report."""
    config = {"hooks": {"pre_build": [["echo", "app"]]}}

    merge_config(config, {"hooks": hooks})

    assert config == {"hooks": hooks}


def test_merge_hooks_table_after_not_a_table():
    """A hooks table merged over a value that isn't a table keeps that value, for
    validation to report."""
    config = {"hooks": [["ruby", "patch.rb", "--verbose"]]}

    merge_config(config, {"hooks": {"post_create": [["echo", "ios"]]}})

    assert config == {"hooks": [["ruby", "patch.rb", "--verbose"]]}
