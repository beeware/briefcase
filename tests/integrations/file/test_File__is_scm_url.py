import pytest


@pytest.mark.parametrize(
    ("path", "is_url"),
    [
        # Files and file-like things
        ("/path/to/file.txt", False),
        ("path/to/file.txt", False),
        ("file.txt", False),
        # URLs
        ("http://example.com", True),
        ("https://example.com", True),
        ("http://github.com/example/repo", True),
        ("https://github.com/example/repo", True),
        ("file://github.com/example/repo", True),
        ("ftp://github.com/example/repo", True),
        ("git+file://github.com/example/repo", True),
        ("git+https://github.com/example/repo", True),
        ("git+ssh://github.com/example/repo", True),
        ("git+http://github.com/example/repo", True),
        ("git+git://github.com/example/repo", True),
        ("git://github.com/example/repo", True),
        ("hg+file://github.com/example/repo", True),
        ("hg+http://github.com/example/repo", True),
        ("hg+https://github.com/example/repo", True),
        ("hg+ssh://github.com/example/repo", True),
        ("hg+static-http://github.com/example/repo", True),
        ("svn://github.com/example/repo", True),
        ("svn+svn://github.com/example/repo", True),
        ("svn+http://github.com/example/repo", True),
        ("svn+https://github.com/example/repo", True),
        ("svn+ssh://github.com/example/repo", True),
        ("bzr+http://github.com/example/repo", True),
        ("bzr+https://github.com/example/repo", True),
        ("bzr+ssh://github.com/example/repo", True),
        ("bzr+sftp://github.com/example/repo", True),
        ("bzr+ftp://github.com/example/repo", True),
        ("bzr+lp://github.com/example/repo", True),
    ],
)
def test_is_scm_url(mock_tools, path, is_url):
    """URLs can be identified."""
    assert mock_tools.file.is_scm_url(path) == is_url
