from briefcase.commands.base import full_kwargs


def test_no_state():
    "If there's no state, just kwargs are returned"
    assert full_kwargs(None, {'a': 1, 'b': 2}) == {
        'a': 1, 'b': 2
    }


def test_state():
    "If there's state, it is added to kwargs"
    assert full_kwargs({'c': 3, 'd': 4}, {'a': 1, 'b': 2}) == {
        'a': 1, 'b': 2, 'c': 3, 'd': 4
    }


def test_state_with_overlap():
    "If theres overlap between state and kwargs, state takes precedence."
    assert full_kwargs({'a': 3, 'd': 4}, {'a': 1, 'b': 2}) == {
        'a': 3, 'b': 2, 'd': 4
    }
