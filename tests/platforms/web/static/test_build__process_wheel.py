import zipfile
from pathlib import Path

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.web.static import StaticWebBuildCommand

from ....utils import create_wheel


@pytest.fixture
def build_command(dummy_console, tmp_path):
    return StaticWebBuildCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_process_wheel(build_command, tmp_path):
    """A wheel can be processed to have CSS content extracted."""

    # Create a wheel with some content
    wheel_filename = create_wheel(
        tmp_path,
        extra_content=[
            # Three CSS files
            (
                "dummy/static/first.css",
                "span {\n  font-color: red;\n  font-size: larger\n}\n",
            ),
            (
                "dummy/static/second.css",
                "div {\n  padding: 10px\n}\n",
            ),
            (
                "dummy/static/deep/third.css",
                "p {\n  color: red\n}\n",
            ),
            # Content in the static file that isn't CSS
            ("dummy/static/explosions.js", "alert('boom!');"),
            # CSS in a location that isn't the static folder
            ("dummy/other.css", "div.other {\n  margin: 10px\n}\n"),
            ("lost.css", "div.lost {\n  margin: 10px\n}\n"),
        ],
    )

    # Collect into inserts dict
    inserts = {}
    build_command._process_wheel(wheelfile=wheel_filename, inserts=inserts)

    # Legacy CSS should be collected into the briefcase.css "css" insert slot
    assert inserts == {
        "static/css/briefcase.css": {
            "css": {
                "dummy 1.2.3 (legacy static CSS: first.css)": (
                    "span {\n  font-color: red;\n  font-size: larger\n}\n"
                ),
                "dummy 1.2.3 (legacy static CSS: second.css)": (
                    "div {\n  padding: 10px\n}\n"
                ),
                "dummy 1.2.3 (legacy static CSS: deep/third.css)": (
                    "p {\n  color: red\n}\n"
                ),
            }
        }
    }


def test_process_wheel_no_content(build_command, tmp_path):
    """A wheel with no resources can be processed."""

    # Create a wheel with some content, but nothing static to be collected
    wheel_filename = create_wheel(
        tmp_path,
        extra_content=[
            # Content in the static file that isn't CSS
            ("dummy/static/explosions.js", "alert('boom!');"),
            # CSS in a location that isn't the static folder.
            ("dummy/other.css", "div.other {\n  margin: 10px\n}\n"),
            ("lost.css", "div.lost {\n  margin: 10px\n}\n"),
        ],
    )

    inserts = {}
    build_command._process_wheel(wheelfile=wheel_filename, inserts=inserts)

    assert inserts == {}


def test_process_wheel_deploy_inserts(build_command, tmp_path):
    """Deploy inserts are collected into the correct insert slot."""
    wheel_filename = create_wheel(
        tmp_path,
        extra_content=[
            ("dummy/deploy/inserts/index.html~header", "<script>alert('hi')</script>"),
            (
                "dummy/deploy/inserts/static/css/briefcase.css~CSS",
                "body { margin: 0; }",
            ),
        ],
    )

    inserts = {}
    build_command._process_wheel(wheelfile=wheel_filename, inserts=inserts)

    # The index.html header insert exists
    assert "index.html" in inserts
    assert "header" in inserts["index.html"]
    contribs = inserts["index.html"]["header"]
    assert any("<script>" in v for v in contribs.values())

    # The CSS insert exists
    assert "static/css/briefcase.css" in inserts
    assert "CSS" in inserts["static/css/briefcase.css"]
    css_contribs = inserts["static/css/briefcase.css"]["CSS"]
    assert any("body { margin: 0; }" in v for v in css_contribs.values())


def test_process_wheel_legacy_css_warning_once(build_command, tmp_path, monkeypatch):
    """Legacy CSS files trigger a single deprecation warning."""
    wheel_filename = create_wheel(
        tmp_path,
        extra_content=[
            ("dummy/static/one.css", "h1 { color: blue; }"),
            ("dummy/static/two.css", "h2 { color: green; }"),
        ],
    )

    # Check on console.warning to count legacy warnings
    warnings = []
    monkeypatch.setattr(
        build_command.console, "warning", lambda msg: warnings.append(msg)
    )

    inserts = {}
    build_command._process_wheel(wheelfile=wheel_filename, inserts=inserts)

    legacy_msgs = [m for m in warnings if "legacy '/static' CSS detected" in m]
    assert len(legacy_msgs) == 1


def test_process_wheel_non_utf8_insert(build_command, tmp_path):
    """Non-UTF8 deploy insert raises a BriefcaseCommandError."""
    bad = b"\xff\xfe\xfa"
    wheel_path = Path(tmp_path) / "dummy-1.2.3-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr("dummy/deploy/inserts/index.html~header", bad)

    inserts = {}
    with pytest.raises(BriefcaseCommandError, match="insert must be UTF-8 encoded"):
        build_command._process_wheel(wheelfile=wheel_path, inserts=inserts)


def test_process_wheel_non_utf8_legacy_css(build_command, tmp_path):
    """Non-UTF8 legacy CSS raises a BriefcaseCommandError."""
    bad = b"\xff\xfe\xfa"
    wheel_path = Path(tmp_path) / "dummy-1.2.3-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr("dummy/static/bad.css", bad)

    inserts = {}
    with pytest.raises(
        BriefcaseCommandError, match="CSS content must be UTF-8 encoded"
    ):
        build_command._process_wheel(wheelfile=wheel_path, inserts=inserts)


def test_handle_legacy_css_warning_once_and_append(
    build_command, tmp_path, monkeypatch
):
    """Legacy CSS warns once and appends to existing contrib key."""
    wheel_path = Path(tmp_path) / "dummy-1.2.3.whl"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr("dummy/static/one.css", "h1 { x:1; }")

    # Count warnings
    warnings = []
    monkeypatch.setattr(build_command.console, "warning", warnings.append)

    inserts = {}
    with zipfile.ZipFile(wheel_path) as zf:
        # First call - warn
        warned = build_command._handle_legacy_css(
            wheel=zf,
            path=Path("dummy/static/one.css"),
            filename="dummy/static/one.css",
            package_key="pkg 1.0",
            inserts=inserts,
            legacy_css_warning=False,
        )
        # Pre-seed same contrib key to force append on second call
        target_map = inserts.setdefault("static/css/briefcase.css", {}).setdefault(
            "css", {}
        )
        key = "pkg 1.0 (legacy static CSS: one.css)"
        target_map[key] = target_map[key] + "\n/*extra*/"
        # Second call - no additional warning, content appended
        warned = build_command._handle_legacy_css(
            wheel=zf,
            path=Path("dummy/static/one.css"),
            filename="dummy/static/one.css",
            package_key="pkg 1.0",
            inserts=inserts,
            legacy_css_warning=warned,
        )

    # One warning only
    legacy_msgs = [m for m in warnings if "legacy '/static' CSS detected" in m]
    assert len(legacy_msgs) == 1

    # Content appended
    out = inserts["static/css/briefcase.css"]["css"][key]
    assert "h1 { x:1; }" in out and "/*extra*/" in out


def test_handle_insert_register_valid_file(build_command, tmp_path):
    """Valid insert is registered under target/slot."""
    wheel_path = Path(tmp_path) / "dummy-1.2.3.whl"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr("dummy/deploy/inserts/index.html~header", "<s>ok</s>")

    inserts = {}
    with zipfile.ZipFile(wheel_path) as zf:
        build_command._handle_insert(
            wheel=zf,
            parts=Path("dummy/deploy/inserts/index.html~header").parts,
            filename="dummy/deploy/inserts/index.html~header",
            package_key="pkg 1.0",
            inserts=inserts,
        )

    assert "index.html" in inserts and "header" in inserts["index.html"]
    assert any("<s>ok</s>" in v for v in inserts["index.html"]["header"].values())


@pytest.mark.parametrize(
    "entry",
    [
        "dummy/deploy/inserts/",  # Top-level directory entry
        "dummy/deploy/inserts/assets/",  # Nested directory entry
    ],
)
def test_handle_insert_skip_dir_entries(build_command, tmp_path, monkeypatch, entry):
    """Deploy/inserts directory entries are skipped with a debug log.

    Parametrized: runs once for top-level dir and once for nested dir.
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
    assert any("skipping, not a valid insert file" in m for m in debugs)


@pytest.mark.parametrize("mode", ["integration", "unit"])
def missing_tilde_under_deploy_inserts_skipped(
    build_command, tmp_path, monkeypatch, mode
):
    """Files under deploy/inserts without '~' are skipped with a debug log.

    Parametrized: tests both integration path (_process_wheel) and direct unit call.
    """
    # Create a dummy wheel containing an invalid insert file (no "~" in name)
    wheel_filename = Path(tmp_path) / "dummy-1.2.3.whl"
    missing_tilde = "dummy/deploy/inserts/index.html"
    with zipfile.ZipFile(wheel_filename, "w") as zf:
        zf.writestr(missing_tilde, "<div>oops</div>")

    # Capture debug messages
    debugs = []
    monkeypatch.setattr(build_command.console, "debug", debugs.append)

    inserts = {}
    if mode == "integration":
        # Run via full wheel scan, which will delegate to _handle_insert
        build_command._process_wheel(wheelfile=wheel_filename, inserts=inserts)
    else:
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
    with zipfile.ZipFile(wheel_path) as zf:
        # First registration creates contrib entry
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
