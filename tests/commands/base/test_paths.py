import os
import platform
import subprocess
from contextlib import suppress
from pathlib import Path

import pytest

from briefcase.exceptions import BriefcaseCommandError

from .conftest import DummyCommand


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows specific tests")
def test_path_is_realpath(tmp_path):
    """Briefcase's data path matches its realpath.

    For the Windows Store Python, filesystem interaction with
    `%LOCALAPPDATA%` can be redirected to a sandboxed location. However,
    `os.path.realpath()` will reveal such a redirection. This test
    ensures that Briefcase bypasses the sandboxing.
    """
    data_path = Path(os.environ["LOCALAPPDATA"]) / "realpathbase"
    try:
        command = DummyCommand(data_path=data_path)
        assert command.data_path == Path(os.path.realpath(data_path))
    finally:
        with suppress(FileNotFoundError):
            os.rmdir(data_path)


def test_data_path_creation_failure(tmp_path, monkeypatch):
    """An error is raised if the data path cannot be created."""

    def raise_calledprpcesserror(*a, **kw):
        raise subprocess.CalledProcessError(returncode=1, cmd=["mkdir", str(data_path)])

    # On Linux and macOS, use /etc/ to raise an OSError
    data_path = Path("/etc/mydatadir")

    # Patch run() since it's apparently quite difficult to find a
    # location in Windows that is guaranteed to throw an error...
    monkeypatch.setattr(subprocess, "run", raise_calledprpcesserror)

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Failed to create the Briefcase directory to store tools and support files:",
    ):
        DummyCommand(data_path=data_path)


def test_space_in_path(tmp_path):
    """The briefcase data path cannot contain spaces."""
    with pytest.raises(
        BriefcaseCommandError,
        match=r"contains spaces. This will cause problems with some tools",
    ):
        DummyCommand(base_path=tmp_path / "base", data_path=tmp_path / "somewhere bad")


def test_empty_custom_path(monkeypatch, tmp_path):
    """If the environment-specified BRIEFCASE_HOME is defined, but empty, an
    error is raised."""
    monkeypatch.setenv("BRIEFCASE_HOME", "")

    with pytest.raises(
        BriefcaseCommandError,
        match=r"The path specified by BRIEFCASE_HOME does not exist.",
    ):
        DummyCommand(base_path=tmp_path / "base")


def test_custom_path_does_not_exist(monkeypatch, tmp_path):
    """If the environment-specified BRIEFCASE_HOME doesn't exist, an error is
    raised."""
    monkeypatch.setenv("BRIEFCASE_HOME", str(tmp_path / "custom"))

    with pytest.raises(
        BriefcaseCommandError,
        match=r"The path specified by BRIEFCASE_HOME does not exist.",
    ):
        DummyCommand(base_path=tmp_path / "base")


def templated_path_test(
    monkeypatch,
    tmp_path,
    data_path,
    environ_path,
    expected_data_path,
):
    if environ_path:
        monkeypatch.setenv("BRIEFCASE_HOME", environ_path.format(tmp_path=tmp_path))
        Path(environ_path.format(tmp_path=tmp_path)).mkdir(parents=True)
    else:
        monkeypatch.delenv("BRIEFCASE_HOME", raising=False)

    command = DummyCommand(
        base_path=tmp_path / "base",
        data_path=data_path.format(tmp_path=tmp_path) if data_path else None,
    )

    assert command.base_path == tmp_path / "base"
    assert command.data_path.exists()
    assert command.data_path == Path(
        os.path.expanduser(expected_data_path.format(tmp_path=tmp_path))
    )


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS specific tests")
@pytest.mark.parametrize(
    "data_path, environ_path, expected_data_path",
    [
        (  # All default values
            None,
            None,
            "~/Library/Caches/org.beeware.briefcase",
        ),
        (  # Environment variable for the data home
            None,
            "{tmp_path}custom/briefcase/path",
            "{tmp_path}custom/briefcase/path",
        ),
        (  # Explicit paths
            "{tmp_path}path/to/data",
            None,
            "{tmp_path}path/to/data",
        ),
        (  # Explicit paths and an environment variable present
            "{tmp_path}path/to/data",
            "{tmp_path}custom/briefcase/path",
            "{tmp_path}path/to/data",
        ),
    ],
)
def test_macOS_paths(
    monkeypatch,
    tmp_path,
    data_path,
    environ_path,
    expected_data_path,
):
    templated_path_test(
        monkeypatch,
        tmp_path,
        data_path,
        environ_path,
        expected_data_path,
    )


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows specific tests")
@pytest.mark.parametrize(
    "data_path, environ_path, expected_data_path",
    [
        (  # All default values
            None,
            None,
            "~/AppData/Local/BeeWare/briefcase/Cache",
        ),
        (  # Environment variable for the data home
            None,
            "{tmp_path}custom\\briefcase\\path",
            "{tmp_path}custom\\briefcase\\path",
        ),
        (  # Explicit paths
            "{tmp_path}path\\to\\data",
            None,
            "{tmp_path}path\\to\\data",
        ),
        (  # Explicit paths and an environment variable present
            "{tmp_path}path\\to\\data",
            "{tmp_path}\\briefcase\\path",
            "{tmp_path}path\\to\\data",
        ),
    ],
)
def test_windows_paths(
    monkeypatch,
    tmp_path,
    data_path,
    environ_path,
    expected_data_path,
):
    templated_path_test(
        monkeypatch,
        tmp_path,
        data_path,
        environ_path,
        expected_data_path,
    )


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux specific tests")
@pytest.mark.parametrize(
    "data_path, environ_path, expected_data_path",
    [
        (  # All default values
            None,
            None,
            "~/.cache/briefcase",
        ),
        (  # Environment variable for the data home
            None,
            "{tmp_path}custom/briefcase/path",
            "{tmp_path}custom/briefcase/path",
        ),
        (  # Explicit paths
            "{tmp_path}path/to/data",
            None,
            "{tmp_path}path/to/data",
        ),
        (  # Explicit paths and an environment variable present
            "{tmp_path}path/to/data",
            "{tmp_path}custom/briefcase/path",
            "{tmp_path}path/to/data",
        ),
    ],
)
def test_linux_paths(
    monkeypatch,
    tmp_path,
    data_path,
    environ_path,
    expected_data_path,
):
    templated_path_test(
        monkeypatch,
        tmp_path,
        data_path,
        environ_path,
        expected_data_path,
    )
