import pytest

from briefcase.console import Console, Log
from briefcase.platforms.web.static import StaticWebBuildCommand

from ....utils import create_file


@pytest.fixture
def build_command(tmp_path):
    return StaticWebBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_trim_file(build_command, tmp_path):
    "A file can be trimmed at a sentinel"
    filename = tmp_path / "dummy.txt"
    content = [
        "This is before the sentinel.",
        "This is also before the sentinel.",
        " ** This is the sentinel ** ",
        "This is after the sentinel.",
        "This is also after the sentinel.",
    ]

    create_file(filename, "\n".join(content))

    # Trim the file at the sentinel
    build_command._trim_file(filename, sentinel=" ** This is the sentinel ** ")

    # The file contains everything up to and including the sentinel.
    with (filename).open(encoding="utf-8") as f:
        assert f.read() == "\n".join(content[:3]) + "\n"


def test_trim_no_sentinel(build_command, tmp_path):
    "A file that doesn't contain the sentinel is returned as-is"
    filename = tmp_path / "dummy.txt"
    content = [
        "This is before the sentinel.",
        "This is also before the sentinel.",
        "NO SENTINEL HERE",
        "This is after the sentinel.",
        "This is also after the sentinel.",
    ]

    create_file(filename, "\n".join(content))

    # Trim the file at a sentinel
    build_command._trim_file(filename, sentinel=" ** This is the sentinel ** ")

    # The file is unmodified.
    with (filename).open(encoding="utf-8") as f:
        assert f.read() == "\n".join(content)


def test_trim_file_multiple_sentinels(build_command, tmp_path):
    "A file with multiple sentinels is trimmed at the first one"
    filename = tmp_path / "dummy.txt"
    content = [
        "This is before the sentinel.",
        "This is also before the sentinel.",
        " ** This is the sentinel ** ",
        "This is after the first sentinel.",
        "This is also after the first sentinel.",
        " ** This is the sentinel ** ",
        "This is after the second sentinel.",
        "This is also after the second sentinel.",
    ]

    create_file(filename, "\n".join(content))

    # Trim the file at the sentinel
    build_command._trim_file(filename, sentinel=" ** This is the sentinel ** ")

    # The file contains everything up to and including the sentinel.
    with (filename).open(encoding="utf-8") as f:
        assert f.read() == "\n".join(content[:3]) + "\n"


def test_trim_sentinel_last_line(build_command, tmp_path):
    "A file with the sentinel as the last full line isn't a problem"
    filename = tmp_path / "dummy.txt"
    content = [
        "This is before the sentinel.",
        "This is also before the sentinel.",
        " ** This is the sentinel ** ",
    ]

    create_file(filename, "\n".join(content) + "\n")

    # Trim the file at a sentinel
    build_command._trim_file(filename, sentinel=" ** This is the sentinel ** ")

    # The file is unmodified.
    with (filename).open(encoding="utf-8") as f:
        assert f.read() == "\n".join(content) + "\n"


def test_trim_sentinel_EOF(build_command, tmp_path):
    "A file with the sentinel at EOF isn't a problem"
    filename = tmp_path / "dummy.txt"
    content = [
        "This is before the sentinel.",
        "This is also before the sentinel.",
        " ** This is the sentinel ** ",
    ]

    create_file(filename, "\n".join(content))

    # Trim the file at a sentinel
    build_command._trim_file(filename, sentinel=" ** This is the sentinel ** ")

    # The file is unmodified.
    with (filename).open(encoding="utf-8") as f:
        assert f.read() == "\n".join(content)
