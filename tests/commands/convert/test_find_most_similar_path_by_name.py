from pathlib import Path

import pytest

from briefcase.commands.convert import find_most_similar_path_by_name


def test_raises_with_no_paths():
    """An error is raised if find_most_similar_path_by_name gets an empty path list."""
    with pytest.raises(ValueError):
        find_most_similar_path_by_name([], "pathname")


@pytest.mark.parametrize(
    "paths, name, most_similar",
    [
        ([Path("a"), Path("b")], "a", Path("a")),
        ([Path("ab"), Path("ba")], "a", Path("ab")),
        ([Path("b"), Path("c")], "a", Path("b")),
        ([Path("parent/a"), Path("b")], "a", Path("parent/a")),
        ([Path("ab"), Path("parent/a")], "a", Path("parent/a")),
        ([Path("bbbbbbb"), Path("parent/eeee")], "name", Path("parent/eeee")),
        ([Path("name"), Path("parent/other_name")], "other", Path("parent/other_name")),
    ],
)
def test_example(paths, name, most_similar):
    """find_most_similar_path_by_name returns path with the most similar name."""
    returned_path = find_most_similar_path_by_name(paths, name)
    assert returned_path == most_similar
