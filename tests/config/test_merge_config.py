from briefcase.config import BaseConfig, merge_config


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


def test_merge_into_base_config_instance():
    """Merging into a BaseConfig instance updates attributes."""
    config = BaseConfig(formal_name="Old", test_requires=["a"])

    merge_config(
        config,
        {
            "formal_name": "New",
            "test_requires": ["b"],
        },
    )

    assert config.formal_name == "New"
    assert config.test_requires == ["a", "b"]
