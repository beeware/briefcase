from briefcase.integrations.subprocess import ensure_str


def test_ensure_str():
    assert ensure_str("a string 1\na string 2") == "a string 1\na string 2"
    assert ensure_str(b"some bytes 1\nsome bytes 2") == "some bytes 1\nsome bytes 2"
    assert ensure_str(1024) == "1024"
