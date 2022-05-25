import pytest

from briefcase.integrations.subprocess import ensure_str


@pytest.mark.parametrize(
    "indata, output",
    [
        ("a string 1\na string 2", "a string 1\na string 2"),
        (b"some bytes 1\nsome bytes 2", "some bytes 1\nsome bytes 2"),
        (1024, "1024"),
    ],
)
def test_ensure_str(indata, output):
    assert ensure_str(indata) == output
