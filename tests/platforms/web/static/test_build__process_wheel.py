import pytest

from briefcase.console import Console, Log
from briefcase.platforms.web.static import StaticWebBuildCommand

from ....utils import create_file, create_wheel


@pytest.fixture
def build_command(tmp_path):
    return StaticWebBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_process_wheel(build_command, tmp_path):
    """Wheels can have inserted and static content extracted."""
    # Create an existng file from a previous unpack
    create_file(
        tmp_path / "static" / "dummy" / "old" / "existing.css",
        "div.existing {margin: 99px}",
    )

    # Create a wheel with some content.
    wheel_filename = create_wheel(
        tmp_path,
        package="dummy",
        extra_content=[
            # Three CSS files
            ("dummy/inserts/first.css", "div.first {\n  margin: 1px\n}\n"),
            ("dummy/inserts/second.css", "div.second {\n  margin: 2px\n}\n"),
            ("dummy/inserts/deep/third.css", "div.third {\n  margin: 3px\n}\n"),
            # Non-CSS insert content
            ("dummy/inserts/index.html:header", "<link href='logo.png'/>"),
            ("dummy/inserts/deep/index.html:other", "<script>alert('boom!')</script>"),
            # CSS, JS and images in the static folder.
            ("dummy/static/other.css", "div.other {\n  margin: 10px\n}\n"),
            ("dummy/static/deep/more.css", "div.more {\n  margin: 11px\n}\n"),
            # CSS in a location that isn't the static or inserts folder.
            ("dummy/somewhere/somewhere.css", "div.somewhere {\n  margin: 20px\n}\n"),
            ("dummy/extra.css", "div.extra {\n  margin: 21px\n}\n"),
            ("lost.css", "div.lost {\n  margin: 22px\n}\n"),
        ],
    )

    inserts = {}
    build_command._process_wheel(
        wheel_filename,
        inserts=inserts,
        static_path=tmp_path / "static",
    )

    assert inserts == {
        "CSS": {
            "first.css": {"dummy 1.2.3": "div.first {\n  margin: 1px\n}\n"},
            "second.css": {"dummy 1.2.3": "div.second {\n  margin: 2px\n}\n"},
            "deep/third.css": {"dummy 1.2.3": "div.third {\n  margin: 3px\n}\n"},
        },
        "index.html": {
            "header": {"dummy 1.2.3": "<link href='logo.png'/>"},
        },
        "deep/index.html": {
            "other": {"dummy 1.2.3": "<script>alert('boom!')</script>"},
        },
    }

    # Create another wheel with some content.
    wheel_filename = create_wheel(
        tmp_path,
        package="more",
        extra_content=[
            # A new CSS insert
            ("more/inserts/more.css", "div.more {\n  margin: 30px\n}\n"),
            # Another CSS insert with the same name
            ("more/inserts/first.css", "div.first {\n  margin: 31px\n}\n"),
            # A new insert with a new name
            ("more/inserts/other.html:header", "<meta charset='utf-8'>"),
            # A new insert on an existing file
            ("more/inserts/index.html:bootstrap", "<span>hello</span>"),
            # An existing insert on an existing file
            ("more/inserts/index.html:header", "<link href='foo.css'/>"),
            # CSS, JS and images in the static folder.
            ("more/static/more-other.css", "div.other {\n  margin: 10px\n}\n"),
            ("more/static/deep/more-more.css", "div.more {\n  margin: 11px\n}\n"),
        ],
    )

    # Process the additional wheel over the existing wheel
    build_command._process_wheel(
        wheel_filename,
        inserts=inserts,
        static_path=tmp_path / "static",
    )

    assert inserts == {
        "CSS": {
            "first.css": {
                "dummy 1.2.3": "div.first {\n  margin: 1px\n}\n",
                "more 1.2.3": "div.first {\n  margin: 31px\n}\n",
            },
            "second.css": {"dummy 1.2.3": "div.second {\n  margin: 2px\n}\n"},
            "deep/third.css": {"dummy 1.2.3": "div.third {\n  margin: 3px\n}\n"},
            "more.css": {"more 1.2.3": "div.more {\n  margin: 30px\n}\n"},
        },
        "index.html": {
            "header": {
                "dummy 1.2.3": "<link href='logo.png'/>",
                "more 1.2.3": "<link href='foo.css'/>",
            },
            "bootstrap": {"more 1.2.3": "<span>hello</span>"},
        },
        "other.html": {
            "header": {"more 1.2.3": "<meta charset='utf-8'>"},
        },
        "deep/index.html": {
            "other": {"dummy 1.2.3": "<script>alert('boom!')</script>"},
        },
    }

    # Static files all exist in the static location
    assert (tmp_path / "static" / "dummy" / "other.css").exists()
    assert (tmp_path / "static" / "dummy" / "deep" / "more.css").exists()
    assert (tmp_path / "static" / "more" / "more-other.css").exists()
    assert (tmp_path / "static" / "more" / "deep" / "more-more.css").exists()

    # Pre-existing static file no longer exists.
    assert not (tmp_path / "static" / "dummy" / "old" / "existing.css").exists()


def test_process_wheel_no_content(build_command, tmp_path):
    """A wheel with no resources can be processed."""

    # Create a wheel with some content, but nothing static to be collected
    wheel_filename = create_wheel(
        tmp_path,
        extra_content=[
            # CSS in a location that isn't the static folder.
            ("dummy/other.css", "div.other {\n  margin: 10px\n}\n"),
            ("lost.css", "div.lost {\n  margin: 10px\n}\n"),
        ],
    )

    inserts = {}
    build_command._process_wheel(
        wheel_filename, inserts=inserts, static_path=tmp_path / "static"
    )

    assert inserts == {}
