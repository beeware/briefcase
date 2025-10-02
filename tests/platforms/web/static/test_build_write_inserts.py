from pathlib import Path
from textwrap import dedent

import pytest

from briefcase.console import Console
from briefcase.platforms.web.static import StaticWebBuildCommand


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
