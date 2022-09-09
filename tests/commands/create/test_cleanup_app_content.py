import pytest

from ...utils import create_file


@pytest.fixture
def myapp_unrolled(myapp, support_path, app_packages_path_index):
    # Create some files that can be cleaned up
    create_file(support_path / "dir1" / "a_file1.txt", "pork")
    create_file(support_path / "dir1" / "a_file2.doc", "ham")
    create_file(support_path / "dir1" / "b_file.txt", "eggs")
    create_file(support_path / "dir2" / "b_file.txt", "spam")
    create_file(support_path / "other" / "b_file.txt", "wigs")

    return myapp


def test_no_cleanup(create_command, myapp_unrolled, support_path):
    """If there are no cleanup directives, bundle content isn't touched."""

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the files are still there
    assert (support_path / "dir1" / "a_file1.txt").exists()
    assert (support_path / "dir1" / "a_file2.doc").exists()
    assert (support_path / "dir1" / "b_file.txt").exists()
    assert (support_path / "dir2" / "b_file.txt").exists()
    assert (support_path / "other" / "b_file.txt").exists()


def test_dir_cleanup(create_command, myapp_unrolled, support_path):
    """A directory can be cleaned up."""
    myapp_unrolled.cleanup_paths = ["path/to/support/dir1"]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the files in dir1 have been removed
    assert not (support_path / "dir1" / "a_file1.txt").exists()
    assert not (support_path / "dir1" / "a_file2.doc").exists()
    assert not (support_path / "dir1" / "b_file.txt").exists()
    assert (support_path / "dir2" / "b_file.txt").exists()
    assert (support_path / "other" / "b_file.txt").exists()


def test_file_cleanup(create_command, myapp_unrolled, support_path):
    """A single file can be cleaned up."""
    myapp_unrolled.cleanup_paths = ["path/to/support/dir1/a_file1.txt"]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the named file has been removed
    assert not (support_path / "dir1" / "a_file1.txt").exists()
    assert (support_path / "dir1" / "a_file2.doc").exists()
    assert (support_path / "dir1" / "b_file.txt").exists()
    assert (support_path / "dir2" / "b_file.txt").exists()
    assert (support_path / "other" / "b_file.txt").exists()


def test_dir_glob_cleanup(create_command, myapp_unrolled, support_path):
    """A glob of directories can be cleaned up."""
    myapp_unrolled.cleanup_paths = ["path/to/support/dir*"]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the matching directories have been removed
    assert not (support_path / "dir1" / "a_file1.txt").exists()
    assert not (support_path / "dir1" / "a_file2.doc").exists()
    assert not (support_path / "dir1" / "b_file.txt").exists()
    assert not (support_path / "dir2" / "b_file.txt").exists()
    assert (support_path / "other" / "b_file.txt").exists()


def test_file_glob_cleanup(create_command, myapp_unrolled, support_path):
    """A glob of files can be cleaned up."""
    myapp_unrolled.cleanup_paths = ["path/to/support/dir1/*.txt"]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the matching files have been removed
    assert not (support_path / "dir1" / "a_file1.txt").exists()
    assert (support_path / "dir1" / "a_file2.doc").exists()
    assert not (support_path / "dir1" / "b_file.txt").exists()
    assert (support_path / "dir2" / "b_file.txt").exists()
    assert (support_path / "other" / "b_file.txt").exists()


def test_template_glob_cleanup(create_command, myapp_unrolled, support_path):
    """A glob of files specified in the template will be added to the cleanup
    list."""
    # Define a cleanup_paths in the template *and* on the app
    create_command._path_index = {
        myapp_unrolled: {
            "cleanup_paths": ["path/to/support/dir1/a_*.*"],
        }
    }
    myapp_unrolled.cleanup_paths = ["path/to/support/other/*"]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the files from the app config and template config have been removed
    assert not (support_path / "dir1" / "a_file1.txt").exists()
    assert not (support_path / "dir1" / "a_file2.doc").exists()
    assert (support_path / "dir1" / "b_file.txt").exists()
    assert (support_path / "dir2" / "b_file.txt").exists()
    assert not (support_path / "other" / "b_file.txt").exists()


def test_non_existent_cleanup(create_command, myapp_unrolled, support_path):
    """Referencing a specific file that doesn't exist doesn't cause a
    problem."""
    myapp_unrolled.cleanup_paths = [
        # This file exists
        "path/to/support/dir1/a_file1.txt",
        # None of these paths do.
        "path/to/support/dir1/missing.txt",
        "path/to/support/nowhere",
        "path/to/support/absent/*",
    ]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the single existing file named has been removed
    assert not (support_path / "dir1" / "a_file1.txt").exists()
    assert (support_path / "dir1" / "a_file2.doc").exists()
    assert (support_path / "dir1" / "b_file.txt").exists()
    assert (support_path / "dir2" / "b_file.txt").exists()
    assert (support_path / "other" / "b_file.txt").exists()
