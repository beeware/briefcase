import zipfile
from pathlib import Path

import pytest

from briefcase.platforms.web.static import StaticWebBuildCommand


@pytest.fixture
def build_command(dummy_console, tmp_path):
    return StaticWebBuildCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_handle_insert_register_valid_file(build_command, tmp_path):
    """Valid insert is registered under target/slot."""
    wheel_path = Path(tmp_path) / "dummy-1.2.3.whl"
    filename = "dummy/deploy/inserts/index.html~header"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr(filename, "<s>ok</s>")

    inserts = {}
    with zipfile.ZipFile(wheel_path) as zf:
        build_command._handle_insert(
            wheel=zf,
            parts=Path(filename).parts,
            filename=filename,
            package_key="pkg 1.0",
            inserts=inserts,
        )

    assert "index.html" in inserts and "header" in inserts["index.html"]
    assert any("<s>ok</s>" in v for v in inserts["index.html"]["header"].values())


@pytest.mark.parametrize(
    "entry, expected_skip",
    [
        ("dummy/deploy/inserts/", True),  # Top-level directory entry
        ("dummy/deploy/inserts/assets/", False),  # Nested directory entry
    ],
)
def test_handle_insert_skip_dir_entries(
    build_command,
    tmp_path,
    monkeypatch,
    entry,
    expected_skip,
):
    """Deploy/inserts directory entries are skipped with a debug log.

    Parametrised: runs once for top-level dir and once for nested dir.
    """
    # Create a dummy wheel containing the "directory" entry
    wheel_path = Path(tmp_path) / "dummy-1.2.3.whl"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr(entry, "")

    # Capture debug messages
    debugs = []
    monkeypatch.setattr(build_command.console, "debug", debugs.append)

    # Run the handler against this entry
    inserts = {}
    with zipfile.ZipFile(wheel_path) as zf:
        build_command._handle_insert(
            wheel=zf,
            parts=Path(entry).parts,
            filename=entry,
            package_key="pkg 1.0",
            inserts=inserts,
        )

    # Directory entries should be ignored completely
    assert inserts == {}
    # And a debug message explaining the skip should be logged
    if expected_skip:
        assert any("skipping, not a valid insert file" in m for m in debugs)
    else:
        assert all("skipping, not a valid insert file" not in m for m in debugs)


def test_handle_insert_missing_tilde_skipped(
    build_command,
    tmp_path,
    monkeypatch,
):
    """Files under deploy/inserts without '~' are skipped with a debug log."""
    # Create a dummy wheel containing an invalid insert file (no "~" in name)
    wheel_filename = Path(tmp_path) / "dummy-1.2.3.whl"
    missing_tilde = "dummy/deploy/inserts/index.html"
    with zipfile.ZipFile(wheel_filename, "w") as zf:
        zf.writestr(missing_tilde, "<div>oops</div>")

    # Capture debug messages
    debugs = []
    monkeypatch.setattr(build_command.console, "debug", debugs.append)

    inserts = {}
    # Run handler directly on the invalid file
    with zipfile.ZipFile(wheel_filename) as zf:
        build_command._handle_insert(
            wheel=zf,
            parts=Path(missing_tilde).parts,
            filename=missing_tilde,
            package_key="pkg 1.0",
            inserts=inserts,
        )

    # File should be ignored completely
    assert inserts == {}
    # And a debug message should clearly say why (missing "~")
    assert any("must match '<target>~<insert>'" in m for m in debugs)


def test_handle_insert_append_existing_contrib(build_command, tmp_path):
    """Second insert with same contrib key appends with newline."""
    wheel_path = Path(tmp_path) / "dummy-1.2.3.whl"
    filename = "dummy/deploy/inserts/index.html~header"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr(filename, "<first/>")

    inserts = {}
    # First registration creates contrib entry
    with zipfile.ZipFile(wheel_path) as zf:
        build_command._handle_insert(
            wheel=zf,
            parts=Path(filename).parts,
            filename=filename,
            package_key="pkg 1.0",
            inserts=inserts,
        )
        # Second registration appends to same key
        build_command._handle_insert(
            wheel=zf,
            parts=Path(filename).parts,
            filename=filename,
            package_key="pkg 1.0",
            inserts=inserts,
        )

    contribs = inserts["index.html"]["header"]
    contrib_key = next(iter(contribs.keys()))
    value = contribs[contrib_key]

    assert value.count("<first/>") == 2
    assert "\n" in value


def test_handle_insert_non_utf8_raises(
    build_command,
    tmp_path,
):
    """Non-UTF8 insert content raises UnicodeDecodeError."""
    bad = b"\xff\xfe\xfa"
    wheel_path = Path(tmp_path) / "dummy-1.2.3.whl"
    filename = "dummy/deploy/inserts/index.html~header"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr(filename, bad)

    inserts = {}
    with zipfile.ZipFile(wheel_path) as zf, pytest.raises(UnicodeDecodeError):
        build_command._handle_insert(
            wheel=zf,
            parts=Path(filename).parts,
            filename=filename,
            package_key="pkg 1.0",
            inserts=inserts,
        )
