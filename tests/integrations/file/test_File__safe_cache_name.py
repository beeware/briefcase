import pytest

from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize(
    "cache_full_name",
    [
        # A deep content-disposition path
        pytest.param("path/to/something.zip", id="deep-path"),
        # Unix-style relative traversal
        pytest.param(r"../something.zip", id="unix-relative"),
        # Deeper Unix-style traversal
        pytest.param(r"../../../something.zip", id="unix-relative-multiple"),
        # Windows-style relative traversal
        pytest.param(r"..\something.zip", id="win-relative"),
        # Deeper Windows-style traversal
        pytest.param(r"..\..\..\something.zip", id="win-relative-multiple"),
        # Mixed separators
        pytest.param(r"../..\something.zip", id="mixed-separators"),
        # Absolute Windows path
        pytest.param(r"C:\Windows\something.zip", id="win-absolute"),
        # UNC path
        pytest.param(r"\\evil-host\share\something.zip", id="win-unc"),
    ],
)
def test_safe_cache_name(mock_tools, cache_full_name):
    """A server-provided filename containing Windows path separators can't be used to
    write outside the download path; only the final path component is used."""
    assert mock_tools.file._safe_cache_name(cache_full_name) == "something.zip"


@pytest.mark.parametrize(
    "cache_full_name",
    [
        # Parent directory reference
        pytest.param("..", id="parent-dir"),
        # Windows-style parent directory reference
        pytest.param(r"a\..", id="win-parent-dir"),
        # Current directory reference
        pytest.param(".", id="current-dir"),
        # Trailing separator yields an empty name
        pytest.param("path\\", id="trailing-separator"),
        # Windows drive-relative path
        pytest.param("D:something.zip", id="win-drive-relative"),
        # NTFS alternate data stream
        pytest.param("something.zip:stream", id="ntfs-stream"),
        # Long filename
        pytest.param("all work and no play" * 100 + ".zip", id="long-name"),
    ]
    # Windows device names
    + [
        pytest.param(device, id=f"win-{device}")
        for device in ["NUL", "CON", "PRN", "AUX"]
        + [f"COM{i}" for i in "123456789¹²³"]
        + [f"LPT{i}" for i in "123456789¹²³"]
        + ["nul", "nul ", "nul.", "nul.txt", "Nul", "com4.filename.txt"]
    ],
)
def test_invalid_cache_name(mock_tools, cache_full_name):
    """An error is raised if a safe name can't be generated."""
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to determine a safe download filename",
    ):
        mock_tools.file._safe_cache_name(cache_full_name)
