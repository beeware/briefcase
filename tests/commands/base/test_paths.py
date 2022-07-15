import os
import platform
from pathlib import Path

import pytest

from briefcase.exceptions import BriefcaseCommandError

from .conftest import DummyCommand


def test_space_in_path(tmp_path):
    """The briefcase data path cannot contain spaces."""
    with pytest.raises(
        BriefcaseCommandError,
        match=r"contains spaces. This will cause problems with some tools",
    ):
        DummyCommand(tmp_path / "base", data_path=tmp_path / "somewhere bad")


def test_empty_custom_path(monkeypatch, tmp_path):
    """If the environment-specified BRIEFCASE_HOME is defined, but empty, an
    error is raised."""
    monkeypatch.setenv("BRIEFCASE_HOME", "")

    with pytest.raises(
        BriefcaseCommandError,
        match=r"The path specified by BRIEFCASE_HOME does not exist.",
    ):
        DummyCommand(tmp_path / "base")


def test_custom_path_does_not_exist(monkeypatch, tmp_path):
    """If the environment-specified BRIEFCASE_HOME doesn't exist, an error is
    raised."""
    monkeypatch.setenv("BRIEFCASE_HOME", tmp_path / "custom")

    with pytest.raises(
        BriefcaseCommandError,
        match=r"The path specified by BRIEFCASE_HOME does not exist.",
    ):
        DummyCommand(tmp_path / "base")


def templated_path_test(
    monkeypatch,
    tmp_path,
    home_path,
    data_path,
    environ_path,
    expected_home_path,
    expected_data_path,
):
    if environ_path:
        monkeypatch.setenv("BRIEFCASE_HOME", environ_path.format(tmp_path=tmp_path))
        Path(environ_path.format(tmp_path=tmp_path)).mkdir(parents=True)
    else:
        monkeypatch.delenv("BRIEFCASE_HOME", raising=False)

    command = DummyCommand(
        tmp_path / "base",
        home_path=home_path,
        data_path=data_path.format(tmp_path=tmp_path) if data_path else None,
    )
    assert command.base_path == tmp_path / "base"
    assert command.home_path == Path(os.path.expanduser(expected_home_path))
    assert command.data_path == Path(
        os.path.expanduser(expected_data_path.format(tmp_path=tmp_path))
    )


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS specific tests")
@pytest.mark.parametrize(
    "home_path, data_path, environ_path, expected_home_path, expected_data_path",
    [
        (  # All default values
            None,
            None,
            None,
            "~",
            "~/Library/Caches/org.beeware.briefcase",
        ),
        (  # Environment variable for the data home
            None,
            None,
            "{tmp_path}custom/briefcase/path",
            "~",
            "{tmp_path}custom/briefcase/path",
        ),
        (  # Explicit paths
            "/path/to/home",
            "/path/to/data",
            None,
            "/path/to/home",
            "/path/to/data",
        ),
        (  # Explicit paths and an environment variable present
            "/path/to/home",
            "/path/to/data",
            "{tmp_path}custom/briefcase/path",
            "/path/to/home",
            "/path/to/data",
        ),
    ],
)
def test_macOS_paths(
    monkeypatch,
    tmp_path,
    home_path,
    data_path,
    environ_path,
    expected_home_path,
    expected_data_path,
):
    templated_path_test(
        monkeypatch,
        tmp_path,
        home_path,
        data_path,
        environ_path,
        expected_home_path,
        expected_data_path,
    )


@pytest.mark.skipif(platform.system() != "Windows", reason="Windoes specific tests")
@pytest.mark.parametrize(
    "home_path, data_path, environ_path, expected_home_path, expected_data_path",
    [
        (  # All default values
            None,
            None,
            None,
            "~",
            "~/AppData/Local/BeeWare/briefcase/Cache",
        ),
        (  # Environment variable for the data home
            None,
            None,
            "{tmp_path}custom\\briefcase\\path",
            "~",
            "{tmp_path}custom\\briefcase\\path",
        ),
        (  # Explicit paths
            "Y:\\path\\to\\home",
            "Z:\\path\\to\\data",
            None,
            "Y:\\path\\to\\home",
            "Z:\\path\\to\\data",
        ),
        (  # Explicit paths and an environment variable present
            "Y:\\path\\to\\home",
            "Z:\\path\\to\\data",
            "{tmp_path}\\briefcase\\path",
            "Y:\\path\\to\\home",
            "Z:\\path\\to\\data",
        ),
    ],
)
def test_windows_paths(
    monkeypatch,
    tmp_path,
    home_path,
    data_path,
    environ_path,
    expected_home_path,
    expected_data_path,
):
    templated_path_test(
        monkeypatch,
        tmp_path,
        home_path,
        data_path,
        environ_path,
        expected_home_path,
        expected_data_path,
    )


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux specific tests")
@pytest.mark.parametrize(
    "home_path, data_path, environ_path, expected_home_path, expected_data_path",
    [
        (  # All default values
            None,
            None,
            None,
            "~",
            "~/.cache/briefcase",
        ),
        (  # Environment variable for the data home
            None,
            None,
            "{tmp_path}custom/briefcase/path",
            "~",
            "{tmp_path}custom/briefcase/path",
        ),
        (  # Explicit paths
            "/path/to/home",
            "/path/to/data",
            None,
            "/path/to/home",
            "/path/to/data",
        ),
        (  # Explicit paths and an environment variable present
            "/path/to/home",
            "/path/to/data",
            "{tmp_path}custom/briefcase/path",
            "/path/to/home",
            "/path/to/data",
        ),
    ],
)
def test_linux_paths(
    monkeypatch,
    tmp_path,
    home_path,
    data_path,
    environ_path,
    expected_home_path,
    expected_data_path,
):
    templated_path_test(
        monkeypatch,
        tmp_path,
        home_path,
        data_path,
        environ_path,
        expected_home_path,
        expected_data_path,
    )
