import zipfile
from pathlib import Path

import pytest

from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.web.static import StaticWebBuildCommand

from ....utils import create_wheel


@pytest.fixture
def build_command(tmp_path):
    return StaticWebBuildCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_process_wheel(build_command, tmp_path):
    """A wheel can be processed to have CSS content extracted."""

    # Create a wheel with some content.
    wheel_filename = create_wheel(
        tmp_path,
        extra_content=[
            # Two CSS files
            (
                "dummy/static/first.css",
                "span {\n  font-color: red;\n  font-size: larger\n}\n",
            ),
            ("dummy/static/second.css", "div {\n  padding: 10px\n}\n"),
            ("dummy/static/deep/third.css", "p {\n  color: red\n}\n"),
            # Content in the static file that isn't CSS
            ("dummy/static/explosions.js", "alert('boom!');"),
            # CSS in a location that isn't the static folder.
            ("dummy/other.css", "div.other {\n  margin: 10px\n}\n"),
            ("lost.css", "div.lost {\n  margin: 10px\n}\n"),
        ],
    )

    # Collect into inserts dict
    inserts = {}
    build_command._process_wheel(wheelfile=wheel_filename, inserts=inserts)

    # Legacy CSS should be collected into the briefcase.css "CSS" insert slot
    assert inserts == {
        "static/css/briefcase.css": {
            "CSS": {
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


def test_process_wheel_invalid_insert_skipped(build_command, tmp_path, monkeypatch):
    """Files without '~' in their name under deploy/inserts are skipped."""
    wheel_filename = create_wheel(
        tmp_path,
        extra_content=[
            ("dummy/deploy/inserts/index.html", "<div>oops</div>"),
        ],
    )

    # Check on console.debug to confirm a skip message was emitted
    seen = {"debugs": []}
    monkeypatch.setattr(
        build_command.console, "debug", lambda msg: seen["debugs"].append(msg)
    )

    inserts = {}
    build_command._process_wheel(wheelfile=wheel_filename, inserts=inserts)

    assert inserts == {}
    assert any(
        "skipping" in msg and "must match '<target>~<insert>'" in msg
        for msg in seen["debugs"]
    )


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
