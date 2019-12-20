from briefcase.config import merge_config


def test_merge_no_options_no_data():
    "If there are no initial options or new additional options, nothing changes"
    config = {'other': 1234}

    merge_config(config, {})

    assert config == {'other': 1234}


def test_merge_no_data():
    "If there are no new options, nothing changes"
    config = {
        'requires': ['first', 'second'],
        'other': 1234,
    }

    merge_config(config, {})

    assert config == {
        'requires': ['first', 'second'],
        'other': 1234,
    }


def test_merge_no_option():
    "If there are no existing options, the new option become the entire value."
    config = {'other': 1234}

    merge_config(config, {'requires': ['third', 'fourth']})

    assert config == {
        'requires': ['third', 'fourth'],
        'other': 1234,
    }


def test_merge():
    "If there are existing options and new options, merge."
    config = {
        'requires': ['first', 'second'],
        'other': 1234
    }

    merge_config(config, {'requires': ['third', 'fourth'], 'other': 5678})

    assert config == {
        'requires': ['first', 'second', 'third', 'fourth'],
        'other': 5678,
    }


def test_convert_base_definition():
    "The merge operation succeeds when called on itself"
    config = {
        'requires': ['first', 'second'],
        'other': 1234,
    }

    merge_config(config, config)

    assert config == {
        'requires': ['first', 'second'],
        'other': 1234,
    }


def test_merged_keys():
    "There are multiple mergeable keys."
    config = {
        'requires': ['first', 'second'],
        'sources': ['a', 'b'],
        'non-merge': ['1', '2'],
        'other': 1234
    }

    merge_config(config, {
        'requires': ['third', 'fourth'],
        'sources': ['c', 'd'],
        'non-merge': ['3', '4'],
    })

    assert config == {
        'requires': ['first', 'second', 'third', 'fourth'],
        'sources': ['a', 'b', 'c', 'd'],
        'non-merge': ['3', '4'],
        'other': 1234,
    }
