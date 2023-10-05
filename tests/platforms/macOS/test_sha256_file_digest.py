from briefcase.platforms.macOS.utils import sha256_file_digest

from ...utils import create_file


def test_sha256_file_digest(tmp_path):
    """A sha256 digest can be computed for a file."""
    # Create a file
    create_file(tmp_path / "content.txt", b"Hello world\nGoodbye world.\n", mode="wb")

    # A sha256 digest is returned.
    assert sha256_file_digest(tmp_path / "content.txt") == (
        "8c9b99fbb457c5dfc4553ef9ba9e7e2c55baaaf2fec35897c4bfb4fd2895a5f7"
    )
