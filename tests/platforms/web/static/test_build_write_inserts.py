from pathlib import Path
from textwrap import dedent

import pytest

from briefcase.console import Console
from briefcase.platforms.web.static import CSS_BANNER, StaticWebBuildCommand


@pytest.fixture
def build_command(tmp_path):
    return StaticWebBuildCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.fixture
def app_config(first_app_config, tmp_path):
    first_app_config._path = tmp_path / "base_path/build/first-app/web/static"
    (first_app_config._path / "www").mkdir(parents=True)
    return first_app_config


def write_target_file(base_path, rel_filename, content):
    target = base_path / "www" / rel_filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def test_write_insert_warn_if_slot_missing(build_command, app_config, monkeypatch):
    """Warn if insert slot markers are missing from the file."""

    # File without insert markers
    file_text = "<html>No markers here</html>"
    target = write_target_file(app_config._path, "index.html", file_text)

    # Capture warnings
    warnings = []
    monkeypatch.setattr(build_command.console, "warning", warnings.append)

    # Attempt to insert into missing slot
    inserts = {"header": {"pkg": "<div/>"}}
    build_command.write_inserts(app_config, Path("index.html"), inserts)

    # Ensure warning was raised and file is unchanged
    assert any("markers not found" in w for w in warnings)
    assert target.read_text() == file_text


def test_write_insert_warn_if_file_missing(build_command, app_config, monkeypatch):
    """Warn if the target file does not exist."""

    # Capture warnings
    warnings = []
    monkeypatch.setattr(build_command.console, "warning", warnings.append)

    # Attempt to insert into a file that doesn’t exist
    inserts = {"header": {"pkg": "<div/>"}}
    build_command.write_inserts(app_config, Path("notexist.html"), inserts)

    # Ensure warning was raised
    assert any("Target notexist.html not found" in w for w in warnings)


def test_write_insert_is_idempotent(build_command, app_config):
    """Inserts should be idempotent when run multiple times."""

    # File with placeholder slot
    file_text = dedent(
        """\
        <html>
        <!--@@ header:start @@-->
        PLACEHOLDER
        <!--@@ header:end @@-->
        </html>
        """
    )
    target = write_target_file(app_config._path, "index.html", file_text)

    # Apply insert once
    inserts = {"header": {"pkg": "<p>Hello</p>"}}
    build_command.write_inserts(app_config, Path("index.html"), inserts)
    once = target.read_text()

    # Apply insert again
    build_command.write_inserts(app_config, Path("index.html"), inserts)
    twice = target.read_text()

    # Ensure result did not change
    assert once == twice


def test_write_insert_slot_name_regex_escaped(build_command, app_config):
    """Slots containing regex chars should be escaped and matched literally."""

    # File with marker containing regex chars
    file_text = dedent(
        """\
        <html>
        <!--@@ head[er]:start @@-->
        PLACEHOLDER
        <!--@@ head[er]:end @@-->
        </html>
        """
    )
    target = write_target_file(app_config._path, "index.html", file_text)

    # Insert into regex-like slot name
    inserts = {"head[er]": {"pkg": "<p>works</p>"}}
    build_command.write_inserts(app_config, Path("index.html"), inserts)

    # Ensure content was inserted correctly
    out = target.read_text()
    assert "works" in out


def test_write_insert_css_packages_sorted(build_command, app_config):
    """Multiple CSS contributions should be inserted in sorted order."""

    # File with CSS marker slot
    file_text = "/*@@ css:start @@*/\nold\n/*@@ css:end @@*/\n"
    target = write_target_file(app_config._path, "static/css/briefcase.css", file_text)

    # Insert two contributions out of order
    inserts = {"css": {"b": "b{}", "a": "a{}"}}
    build_command.write_inserts(app_config, Path("static/css/briefcase.css"), inserts)

    out = target.read_text()
    a_block = CSS_BANNER.format(package="a", content="a{}")
    b_block = CSS_BANNER.format(package="b", content="b{}")

    # Ensure alphabetical order and removal of old content
    assert out.index(a_block) < out.index(b_block)
    assert "old" not in out


def test_write_insert_replaces_all_matches(build_command, app_config):
    """All matching slots should be replaced, not just the first occurrence."""

    # File with two identical slots
    file_text = (
        "<!--@@ h:start @@-->X<!--@@ h:end @@-->\n"
        "<!--@@ h:start @@-->Y<!--@@ h:end @@-->\n"
    )
    target = write_target_file(app_config._path, "index.html", file_text)

    # Insert replacement content
    inserts = {"h": {"pkg": "Z"}}
    build_command.write_inserts(app_config, Path("index.html"), inserts)

    out = target.read_text()

    # Both occurrences replaced
    assert "X" not in out and "Y" not in out
    assert out.count("Z") == 2


def test_write_insert_handles_html_and_css_markers(build_command, app_config):
    """HTML and CSS marker styles should both be processed in one file."""

    # File containing both HTML and CSS markers
    file_text = dedent("""\
        <html>
          <!--@@ assets:start @@-->
          OLD_HTML
          <!--@@ assets:end @@-->
          <style>
          /*@@ assets:start @@*/
          OLD_CSS
          /*@@ assets:end @@*/
          </style>
        </html>
    """)
    target = write_target_file(app_config._path, "index.html", file_text)

    # Insert HTML and CSS contributions
    inserts = {"assets": {"pkgA": "<link/>", "pkgB": "h1{}"}}
    build_command.write_inserts(app_config, Path("index.html"), inserts)

    out = target.read_text()

    # Ensure both banners appear, new content is inserted, and old content removed
    assert "<!--------------------------------------------------" in out
    assert "<link/>" in out
    assert "/**************************************************" in out
    assert "h1{}" in out
    assert "OLD_HTML" not in out and "OLD_CSS" not in out


def test_write_insert_preserves_multiline_indent(build_command, app_config):
    """Inserted multiline content should preserve indentation of markers."""

    # File with indented marker slot
    file_text = "    <!--@@ header:start @@-->\n    X\n    <!--@@ header:end @@-->\n"
    target = write_target_file(app_config._path, "index.html", file_text)

    # Insert multiline content
    inserts = {"header": {"pkg": "L1\nL2"}}
    build_command.write_inserts(app_config, Path("index.html"), inserts)

    out = target.read_text()

    # Ensure inserted lines are indented properly
    assert "\n    L1\n    L2\n" in out


def test_write_insert_ignores_empty_contributions(build_command, app_config):
    """Empty insert contributions should be ignored (no banner written)."""

    # File with CSS marker slot
    file_text = "/*@@ css:start @@*/\nX\n/*@@ css:end @@*/\n"
    target = write_target_file(app_config._path, "static/css/briefcase.css", file_text)

    # Provide empty contribution
    inserts = {"css": {"pkg": ""}}
    build_command.write_inserts(app_config, Path("static/css/briefcase.css"), inserts)

    out = target.read_text()

    # Ensure no banner for empty contribution
    assert " * pkg" not in out
