from io import StringIO

import pytest

from briefcase.console import Console, Log
from briefcase.platforms.web.static import StaticWebBuildCommand

from ....utils import create_wheel


@pytest.fixture
def build_command(tmp_path):
    return StaticWebBuildCommand(
        logger=Log(),
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

    # Create a dummy css file
    css_file = StringIO()

    build_command._process_wheel(wheel_filename, css_file=css_file)

    assert (
        css_file.getvalue()
        == "\n".join(
            [
                "",
                "/*******************************************************",
                " * dummy 1.2.3::first.css",
                " *******************************************************/",
                "",
                "span {",
                "  font-color: red;",
                "  font-size: larger",
                "}",
                "",
                "/*******************************************************",
                " * dummy 1.2.3::second.css",
                " *******************************************************/",
                "",
                "div {",
                "  padding: 10px",
                "}",
                "",
                "/*******************************************************",
                " * dummy 1.2.3::deep/third.css",
                " *******************************************************/",
                "",
                "p {",
                "  color: red",
                "}",
            ]
        )
        + "\n"
    )


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

    # Create a dummy css file
    css_file = StringIO()

    build_command._process_wheel(wheel_filename, css_file=css_file)

    assert css_file.getvalue() == ""
