import pytest

from briefcase.config import is_pep440_canonical_version, parsed_version


@pytest.mark.parametrize(
    ("version", "parsed"),
    [
        (
            "0.1",
            {
                "epoch": None,
                "release": (0, 1),
                "pre": None,
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.2",
            {
                "epoch": None,
                "release": (1, 2),
                "pre": None,
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.2a3",
            {
                "epoch": None,
                "release": (1, 2),
                "pre": ("a", 3),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.2a13",
            {
                "epoch": None,
                "release": (1, 2),
                "pre": ("a", 13),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.2b4",
            {
                "epoch": None,
                "release": (1, 2),
                "pre": ("b", 4),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.2b14",
            {
                "epoch": None,
                "release": (1, 2),
                "pre": ("b", 14),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.2rc5",
            {
                "epoch": None,
                "release": (1, 2),
                "pre": ("rc", 5),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.2rc15",
            {
                "epoch": None,
                "release": (1, 2),
                "pre": ("rc", 15),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.2.dev6",
            {
                "epoch": None,
                "release": (1, 2),
                "pre": None,
                "post": None,
                "dev": 6,
            },
        ),
        (
            "1.2.dev16",
            {
                "epoch": None,
                "release": (1, 2),
                "pre": None,
                "post": None,
                "dev": 16,
            },
        ),
        (
            "1.2.post8",
            {
                "epoch": None,
                "release": (1, 2),
                "pre": None,
                "post": 8,
                "dev": None,
            },
        ),
        (
            "1.2.post18",
            {
                "epoch": None,
                "release": (1, 2),
                "pre": None,
                "post": 18,
                "dev": None,
            },
        ),
        (
            "1.2.3",
            {
                "epoch": None,
                "release": (1, 2, 3),
                "pre": None,
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.0.2a3",
            {
                "epoch": None,
                "release": (1, 0, 2),
                "pre": ("a", 3),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.0.2a13",
            {
                "epoch": None,
                "release": (1, 0, 2),
                "pre": ("a", 13),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.0.2b4",
            {
                "epoch": None,
                "release": (1, 0, 2),
                "pre": ("b", 4),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.0.2b14",
            {
                "epoch": None,
                "release": (1, 0, 2),
                "pre": ("b", 14),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.0.2rc5",
            {
                "epoch": None,
                "release": (1, 0, 2),
                "pre": ("rc", 5),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.0.2rc15",
            {
                "epoch": None,
                "release": (1, 0, 2),
                "pre": ("rc", 15),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.0.2.dev6",
            {
                "epoch": None,
                "release": (1, 0, 2),
                "pre": None,
                "post": None,
                "dev": 6,
            },
        ),
        (
            "1.0.2.dev16",
            {
                "epoch": None,
                "release": (1, 0, 2),
                "pre": None,
                "post": None,
                "dev": 16,
            },
        ),
        (
            "1.0.2.post7",
            {
                "epoch": None,
                "release": (1, 0, 2),
                "pre": None,
                "post": 7,
                "dev": None,
            },
        ),
        (
            "1.0.2.post17",
            {
                "epoch": None,
                "release": (1, 0, 2),
                "pre": None,
                "post": 17,
                "dev": None,
            },
        ),
        # Date based
        (
            "2019.1",
            {
                "epoch": None,
                "release": (2019, 1),
                "pre": None,
                "post": None,
                "dev": None,
            },
        ),
        (
            "2019.18",
            {
                "epoch": None,
                "release": (2019, 18),
                "pre": None,
                "post": None,
                "dev": None,
            },
        ),
        (
            "25.09.2",
            {
                "epoch": None,
                "release": (25, 9, 2),
                "pre": None,
                "post": None,
                "dev": None,
            },
        ),
        # Examples
        (
            "1.0.dev56",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": None,
                "post": None,
                "dev": 56,
            },
        ),
        (
            "1.0a1",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": ("a", 1),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.0a2.dev56",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": ("a", 2),
                "post": None,
                "dev": 56,
            },
        ),
        (
            "1.0a12.dev56",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": ("a", 12),
                "post": None,
                "dev": 56,
            },
        ),
        (
            "1.0a12",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": ("a", 12),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.0b1.dev56",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": ("b", 1),
                "post": None,
                "dev": 56,
            },
        ),
        (
            "1.0b2",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": ("b", 2),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.0b2.post34.dev56",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": ("b", 2),
                "post": 34,
                "dev": 56,
            },
        ),
        (
            "1.0b2.post34",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": ("b", 2),
                "post": 34,
                "dev": None,
            },
        ),
        (
            "1.0rc1.dev56",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": ("rc", 1),
                "post": None,
                "dev": 56,
            },
        ),
        (
            "1.0rc1",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": ("rc", 1),
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.0",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": None,
                "post": None,
                "dev": None,
            },
        ),
        (
            "1.0.post45.dev34",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": None,
                "post": 45,
                "dev": 34,
            },
        ),
        (
            "1.0.post45",
            {
                "epoch": None,
                "release": (1, 0),
                "pre": None,
                "post": 45,
                "dev": None,
            },
        ),
        (
            "1.1.dev1",
            {
                "epoch": None,
                "release": (1, 1),
                "pre": None,
                "post": None,
                "dev": 1,
            },
        ),
        # Epochs
        (
            "1!2.3",
            {
                "epoch": 1,
                "release": (2, 3),
                "pre": None,
                "post": None,
                "dev": None,
            },
        ),
        (
            "2!1.0a1",
            {
                "epoch": 2,
                "release": (1, 0),
                "pre": ("a", 1),
                "post": None,
                "dev": None,
            },
        ),
        (
            "31!1.0b2.post34.dev56",
            {
                "epoch": 31,
                "release": (1, 0),
                "pre": ("b", 2),
                "post": 34,
                "dev": 56,
            },
        ),
    ],
)
def test_valid_app_version(version, parsed):
    assert is_pep440_canonical_version(version)
    assert parsed == parsed_version(version).__dict__
