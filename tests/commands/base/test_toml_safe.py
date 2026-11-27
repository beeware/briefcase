from pathlib import Path

import pytest

from briefcase.commands.base import toml_safe


@pytest.mark.parametrize(
    ("input", "output"),
    [
        # None handling
        pytest.param(None, "<::NONE::>", id="None"),
        # Primitives
        pytest.param(42, 42, id="int"),
        pytest.param(2.718, pytest.approx(2.718), id="float"),
        pytest.param(True, True, id="bool"),
        pytest.param("hello world", "hello world", id="bool"),
        # Simple collections
        pytest.param([1, 2, 3], [1, 2, 3], id="list"),
        pytest.param((1, 2, 3), [1, 2, 3], id="tuple"),
        pytest.param({"a": 1, "b": 2}, {"a": 1, "b": 2}, id="dict"),
        # Non-primitive
        pytest.param(
            Path("/path/to/file.txt"), "/path/to/file.txt", id="non-primitive"
        ),
        # Nested collections
        pytest.param(
            [1, 2, (3, 4, [None, Path("/path/to/file.txt")])],
            [1, 2, [3, 4, ["<::NONE::>", "/path/to/file.txt"]]],
            id="nested-list",
        ),
        pytest.param(
            {
                "primitive": {"int": 42, "float": 2.718},
                "collection": {
                    "list": [1, 2, None],
                    "tuple": (3, 4, None),
                },
            },
            {
                "primitive": {"int": 42, "float": 2.718},
                "collection": {
                    "list": [1, 2, "<::NONE::>"],
                    "tuple": [3, 4, "<::NONE::>"],
                },
            },
            id="nested-dict",
        ),
    ],
)
def test_toml_safe(input, output):
    """Values can be made TOML-safe."""
    assert toml_safe(input) == output
