import os

import pytest

from briefcase.utils import is_local_path


@pytest.mark.parametrize(
    "altsep, requirement, expected",
    [
        (None, "asdf/xcvb", True),
        (None, "asdf>xcvb", False),
        (">", "asdf/xcvb", True),
        (">", "asdf>xcvb", True),
        (">", "asdf+xcvb", False),
    ],
)
def test_is_local_path_altsep_respected(
    altsep,
    requirement,
    expected,
    monkeypatch,
):
    """``os.altsep`` is included as a separator when available."""
    monkeypatch.setattr(os, "sep", "/")
    monkeypatch.setattr(os, "altsep", altsep)
    assert is_local_path(requirement) is expected
