import pytest

from briefcase.console import Console
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
