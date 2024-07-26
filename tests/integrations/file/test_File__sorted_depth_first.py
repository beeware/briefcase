import pytest

from briefcase.integrations.file import File

from ...utils import create_file


@pytest.mark.parametrize(
    "files, sorted",
    [
        # Files in a directory are sorted lexically
        (
            ["foo/bar/a.txt", "foo/bar/c.txt", "foo/bar/b.txt"],
            ["foo/bar/c.txt", "foo/bar/b.txt", "foo/bar/a.txt"],
        ),
        # Subfolders are sorted before files in that directory; but sorted lexically in themselves
        (
            [
                "foo/bar/b",
                "foo/bar/b/aaa.txt",
                "foo/bar/b/zzz.txt",
                "foo/bar/b/deeper",
                "foo/bar/b/deeper/deeper_db2.txt",
                "foo/bar/b/deeper/deeper_db1.txt",
                "foo/bar/a.txt",
                "foo/bar/c.txt",
                "foo/bar/e.txt",
                "foo/bar/d",
                "foo/bar/d/deep_d2.txt",
                "foo/bar/d/deep_d1.txt",
            ],
            [
                "foo/bar/d/deep_d2.txt",
                "foo/bar/d/deep_d1.txt",
                "foo/bar/b/deeper/deeper_db2.txt",
                "foo/bar/b/deeper/deeper_db1.txt",
                "foo/bar/b/deeper",
                "foo/bar/b/zzz.txt",
                "foo/bar/b/aaa.txt",
                "foo/bar/d",
                "foo/bar/b",
                "foo/bar/e.txt",
                "foo/bar/c.txt",
                "foo/bar/a.txt",
            ],
        ),
        # If a folder contains both folders and files, the folders are returned first.
        (
            [
                "foo/bar/a",
                "foo/bar/b.txt",
                "foo/bar/c",
            ],
            [
                "foo/bar/c",
                "foo/bar/a",
                "foo/bar/b.txt",
            ],
        ),
    ],
)
def test_sorted_depth_first(files, sorted, tmp_path):
    # Convert the strings into paths in the temp folder
    paths = [tmp_path / file_path for file_path in files]

    # Create all the paths that have a suffix
    for file_path in paths:
        if file_path.suffix:
            create_file(tmp_path / file_path, content=str(file_path))
        else:
            file_path.mkdir(parents=True, exist_ok=True)

    assert File.sorted_depth_first(paths) == [
        tmp_path / file_path for file_path in sorted
    ]
