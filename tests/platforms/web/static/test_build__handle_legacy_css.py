import zipfile
from pathlib import Path, PurePosixPath

import pytest

from briefcase.platforms.web.static import StaticWebBuildCommand


@pytest.fixture
def build_command(dummy_console, tmp_path):
    return StaticWebBuildCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_handle_legacy_css_warn_and_append(
    build_command,
    tmp_path,
    capsys,
):
    """Legacy CSS warns and appends to new contrib key."""
    wheel_path = Path(tmp_path) / "dummy-1.2.3.whl"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr("dummy/static/one.css", "h1 { x:1; }")

    inserts = {}
    with zipfile.ZipFile(wheel_path) as zf:
        # First call - warn
        build_command._handle_legacy_css(
            wheel=zf,
            path=PurePosixPath("dummy/static/one.css"),
            package_key="pkg 1.0",
            inserts=inserts,
        )
        # Pre-seed same contrib key to force append on second call
        target_map = inserts.setdefault("static/css/style.css", {}).setdefault(
            "css", {}
        )
        key = "pkg 1.0 (legacy static CSS: one.css)"
        target_map[key] = target_map[key] + "\n/*extra*/"
        # Second call - no additional warning, content appended
        build_command._handle_legacy_css(
            wheel=zf,
            path=PurePosixPath("dummy/static/one.css"),
            package_key="pkg 1.0",
            inserts=inserts,
        )

    # One warning for each file
    output = capsys.readouterr().out
    assert (
        "dummy-1.2.3.whl: legacy '/static' CSS file dummy/static/one.css detected."
        in output
    )

    # Content appended
    out = inserts["static/css/style.css"]["css"][key]
    assert "h1 { x:1; }" in out
    assert "/*extra*/" in out


def test_handle_legacy_css_non_utf8_raise(build_command, tmp_path):
    """Non-UTF8 legacy CSS raises an UnicodeDecodeError."""
    bad = b"\xff\xfe\xfa"
    wheel_path = Path(tmp_path) / "dummy-1.2.3.whl"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr("dummy/static/bad.css", bad)

    inserts = {}
    with zipfile.ZipFile(wheel_path) as zf, pytest.raises(UnicodeDecodeError):
        build_command._handle_legacy_css(
            wheel=zf,
            path=PurePosixPath("dummy/static/bad.css"),
            package_key="pkg 1.0",
            inserts=inserts,
        )
