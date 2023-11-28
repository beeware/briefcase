import pytest

from briefcase.console import LogLevel

from ...utils import create_file


@pytest.fixture
def myapp_unrolled(myapp, support_path, app_packages_path_index):
    # Create some files that can be cleaned up
    create_file(support_path / "dir1/a_file1.txt", "pork")
    create_file(support_path / "dir1/a_file2.doc", "ham")
    create_file(support_path / "dir1/b_file.txt", "eggs")
    create_file(support_path / "dir1/__pycache__/first.pyc", "pyc 1")
    create_file(support_path / "dir1/__pycache__/second.pyc", "pyc 2")
    create_file(support_path / "dir2/b_file.txt", "spam")
    create_file(support_path / "other/deep/b_file.doc", "wigs")
    create_file(support_path / "other/deep/other.doc", "wigs")

    return myapp


@pytest.mark.parametrize("debug", [True, False])
def test_no_cleanup(create_command, myapp_unrolled, support_path, debug, capsys):
    """If there are no cleanup directives, bundle content isn't touched; but __pycache__
    is cleaned."""
    if debug:
        create_command.logger.verbosity = LogLevel.DEBUG

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the files are still there, except for the pycache
    assert (support_path / "dir1/a_file1.txt").exists()
    assert (support_path / "dir1/a_file2.doc").exists()
    assert (support_path / "dir1/b_file.txt").exists()
    assert not (support_path / "dir1/__pycache__").exists()
    assert (support_path / "dir2/b_file.txt").exists()
    assert (support_path / "other/deep/b_file.doc").exists()

    # Console output ends with the done message; the number of other messages depends on
    # whether debug is enabled.
    output = capsys.readouterr().out.split("\n")
    assert output[-3] == "Removing unneeded app bundle content... done"
    assert len(output) == (4 if debug else 3)


@pytest.mark.parametrize("debug", [True, False])
def test_dir_cleanup(create_command, myapp_unrolled, support_path, debug, capsys):
    """A directory can be cleaned up."""
    if debug:
        create_command.logger.verbosity = LogLevel.DEBUG

    myapp_unrolled.cleanup_paths = ["path/to/support/dir1"]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm that dir1 has been removed
    assert not (support_path / "dir1").exists()
    assert (support_path / "dir2/b_file.txt").exists()
    assert (support_path / "other/deep/b_file.doc").exists()

    # Console output ends with the done message; the number of other messages depends on
    # whether debug is enabled.
    output = capsys.readouterr().out.split("\n")
    assert output[-3] == "Removing unneeded app bundle content... done"
    assert len(output) == (4 if debug else 3)


@pytest.mark.parametrize("debug", [True, False])
def test_file_cleanup(create_command, myapp_unrolled, support_path, debug, capsys):
    """A single file can be cleaned up."""
    if debug:
        create_command.logger.verbosity = LogLevel.DEBUG

    myapp_unrolled.cleanup_paths = ["path/to/support/dir1/a_file1.txt"]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the named file (plus __pycache__) has been removed
    assert not (support_path / "dir1/a_file1.txt").exists()
    assert (support_path / "dir1/a_file2.doc").exists()
    assert (support_path / "dir1/b_file.txt").exists()
    assert (support_path / "dir2/b_file.txt").exists()
    assert not (support_path / "dir1/__pycache__").exists()
    assert (support_path / "other/deep/b_file.doc").exists()

    # Console output ends with the done message; the number of other messages depends on
    # whether debug is enabled.
    output = capsys.readouterr().out.split("\n")
    assert output[-3] == "Removing unneeded app bundle content... done"
    assert len(output) == (5 if debug else 3)


@pytest.mark.parametrize("debug", [True, False])
def test_all_files_in_dir_cleanup(
    create_command, myapp_unrolled, support_path, debug, capsys
):
    """All files in a directory can be cleaned up."""
    if debug:
        create_command.logger.verbosity = LogLevel.DEBUG

    myapp_unrolled.cleanup_paths = ["path/to/support/dir1/*"]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the named files (and __pycache__) have been removed,
    # but the dir still exists
    assert not (support_path / "dir1/a_file1.txt").exists()
    assert not (support_path / "dir1/a_file2.doc").exists()
    assert not (support_path / "dir1/b_file.txt").exists()
    assert not (support_path / "dir1/__pycache__").exists()
    assert (support_path / "dir1").exists()
    assert (support_path / "dir2/b_file.txt").exists()
    assert (support_path / "other/deep/b_file.doc").exists()

    # Console output ends with the done message; the number of other messages depends on
    # whether debug is enabled.
    output = capsys.readouterr().out.split("\n")
    assert output[-3] == "Removing unneeded app bundle content... done"
    assert len(output) == (7 if debug else 3)


@pytest.mark.parametrize("debug", [True, False])
def test_dir_glob_cleanup(create_command, myapp_unrolled, support_path, debug, capsys):
    """A glob of directories can be cleaned up."""
    if debug:
        create_command.logger.verbosity = LogLevel.DEBUG

    myapp_unrolled.cleanup_paths = ["path/to/support/dir*"]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the matching directories have been removed
    assert not (support_path / "dir1").exists()
    assert not (support_path / "dir2").exists()
    assert (support_path / "other/deep/b_file.doc").exists()

    # Console output ends with the done message; the number of other messages depends on
    # whether debug is enabled.
    output = capsys.readouterr().out.split("\n")
    assert output[-3] == "Removing unneeded app bundle content... done"
    assert len(output) == (5 if debug else 3)


@pytest.mark.parametrize("debug", [True, False])
def test_file_glob_cleanup(create_command, myapp_unrolled, support_path, debug, capsys):
    """A glob of files can be cleaned up."""
    if debug:
        create_command.logger.verbosity = LogLevel.DEBUG

    myapp_unrolled.cleanup_paths = ["path/to/support/dir1/*.txt"]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the matching files (plus __pycache__) have been removed
    assert not (support_path / "dir1/a_file1.txt").exists()
    assert (support_path / "dir1/a_file2.doc").exists()
    assert not (support_path / "dir1/b_file.txt").exists()
    assert not (support_path / "dir1/__pycache__").exists()
    assert (support_path / "dir2/b_file.txt").exists()
    assert (support_path / "other/deep/b_file.doc").exists()

    # Console output ends with the done message; the number of other messages depends on
    # whether debug is enabled.
    output = capsys.readouterr().out.split("\n")
    assert output[-3] == "Removing unneeded app bundle content... done"
    assert len(output) == (6 if debug else 3)


@pytest.mark.parametrize("debug", [True, False])
def test_deep_glob_cleanup(create_command, myapp_unrolled, support_path, debug, capsys):
    """A glob that matches all directories will be added to the cleanup list."""
    if debug:
        create_command.logger.verbosity = LogLevel.DEBUG

    myapp_unrolled.cleanup_paths = ["path/to/support/**/b_file.*"]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the matching files (plus __pycache__) have been removed
    assert (support_path / "dir1/a_file1.txt").exists()
    assert (support_path / "dir1/a_file2.doc").exists()
    assert not (support_path / "dir1/b_file.txt").exists()
    assert not (support_path / "dir1/__pycache__").exists()
    assert not (support_path / "dir2/b_file.txt").exists()
    assert not (support_path / "other/deep/b_file.doc").exists()
    assert (support_path / "other/deep/other.doc").exists()

    # Console output ends with the done message; the number of other messages depends on
    # whether debug is enabled.
    output = capsys.readouterr().out.split("\n")
    assert output[-3] == "Removing unneeded app bundle content... done"
    assert len(output) == (7 if debug else 3)


@pytest.mark.parametrize("debug", [True, False])
def test_template_glob_cleanup(
    create_command, myapp_unrolled, support_path, debug, capsys
):
    """A glob of files specified in the template will be added to the cleanup list."""
    if debug:
        create_command.logger.verbosity = LogLevel.DEBUG

    # Define a cleanup_paths in the template *and* on the app
    create_command._briefcase_toml[myapp_unrolled] = {
        "paths": {
            "cleanup_paths": ["path/to/support/dir1/a_*.*"],
        }
    }
    myapp_unrolled.cleanup_paths = ["path/to/support/other/*"]

    # Cleanup app content
    create_command.cleanup_app_content(myapp_unrolled)

    # Confirm the files from the app config and template config have been
    # removed, as well as __pycache__
    assert not (support_path / "dir1/a_file1.txt").exists()
    assert not (support_path / "dir1/a_file2.doc").exists()
    assert (support_path / "dir1/b_file.txt").exists()
    assert not (support_path / "dir1/__pycache__").exists()
    assert (support_path / "dir2/b_file.txt").exists()
    assert not (support_path / "other/deep/b_file.doc").exists()

    # Console output ends with the done message; the number of other messages depends on
    # whether debug is enabled.
    output = capsys.readouterr().out.split("\n")
    assert output[-3] == "Removing unneeded app bundle content... done"
    assert len(output) == (7 if debug else 3)


@pytest.mark.parametrize("debug", [True, False])
def test_non_existent_cleanup(
    create_command,
    myapp_unrolled,
    support_path,
    debug,
    capsys,
):
    """Referencing a specific file that doesn't exist doesn't cause a problem."""
    if debug:
        create_command.logger.verbosity = LogLevel.DEBUG

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

    # Confirm the single existing file named has been removed,
    # as well as __pycache__
    assert not (support_path / "dir1/a_file1.txt").exists()
    assert (support_path / "dir1/a_file2.doc").exists()
    assert (support_path / "dir1/b_file.txt").exists()
    assert not (support_path / "dir1/__pycache__").exists()
    assert (support_path / "dir2/b_file.txt").exists()
    assert (support_path / "other/deep/b_file.doc").exists()

    # Console output ends with the done message; the number of other messages depends on
    # whether debug is enabled.
    output = capsys.readouterr().out.split("\n")
    assert output[-3] == "Removing unneeded app bundle content... done"
    assert len(output) == (5 if debug else 3)
