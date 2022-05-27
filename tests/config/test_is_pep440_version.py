import pytest

from briefcase.config import is_pep440_canonical_version, parsed_version


@pytest.mark.parametrize(
    "version, parsed",
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


@pytest.mark.parametrize(
    "version",
    [
        "foobar",  # Really not a version.
        "0xcafe",  # Hex version
        # PEP440 allows for certain variations, but considers them
        # non-canonical. We reject *all* non-canonical.
        # Versions are normalized to lower case
        "1.2RC3",
        "1.2.3.DEV4",
        # Some dashes, underscores and dots are normalized
        "1.0.2.a3",
        "1.0.2-a3",
        "1.0.2_a3",
        "1.0.2.b14",
        "1.0.2-b14",
        "1.0.2_b14",
        "1.0.2.rc15",
        "1.0.2-rc15",
        "1.0.2_rc15",
        "1.0.2dev6",
        "1.0.2post7",
        "1.0.2-dev6",
        "1.0.2_dev6",
        "1.0.2-post7",
        "1.0.2_post7",
        # Other spellings of a/b/rc/pre/post
        "1.0.2alpha7",
        "1.0.2beta7",
        "1.0.2c7",
        "1.0.2preview7",
        "1.0.2r7",
        "1.0.2-7",
        # Local version segments
        "1.0+abc.5",
        "1.0+abc.7",
        "1.0+5",
        "1.0+ubuntu-1",
        # v Prefix,
        "v1.0",
        "v1.2.3.dev4",
    ],
)
def test_invalid_app_version(version):
    assert not is_pep440_canonical_version(version)
