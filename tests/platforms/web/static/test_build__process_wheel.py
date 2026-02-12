import pytest

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

    # Legacy CSS should be collected into the style.css "css" insert slot
    assert inserts == {
        "static/css/style.css": {
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
                "dummy/deploy/inserts/static/css/style.css~CSS",
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
    assert "static/css/style.css" in inserts
    assert "CSS" in inserts["static/css/style.css"]
    css_contribs = inserts["static/css/style.css"]["CSS"]
    assert any("body { margin: 0; }" in v for v in css_contribs.values())


def test_process_wheel_legacy_css_warn_once(build_command, tmp_path, capsys):
    """Legacy CSS files trigger a single deprecation warning."""
    wheel_filename = create_wheel(
        tmp_path,
        extra_content=[
            ("dummy/static/one.css", "h1 { color: blue; }"),
            ("dummy/static/two.css", "h2 { color: green; }"),
        ],
    )

    inserts = {}
    build_command._process_wheel(wheelfile=wheel_filename, inserts=inserts)

    output = capsys.readouterr().out
    assert (
        "dummy-1.2.3-py3-none-any.whl: legacy '/static' CSS file "
        "dummy/static/one.css detected."
        in output
    )
    assert (
        "dummy-1.2.3-py3-none-any.whl: legacy '/static' CSS file "
        "dummy/static/two.css detected."
        in output
    )
