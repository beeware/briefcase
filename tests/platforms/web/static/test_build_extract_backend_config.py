import shutil
import subprocess
import sys
from unittest import mock

if sys.version_info >= (3, 11):  # pragma: no-cover-if-lt-py311
    import tomllib
else:  # pragma: no-cover-if-gte-py311
    import tomli as tomllib

import pytest

from briefcase.console import LogLevel
from briefcase.exceptions import BriefcaseCommandError, BriefcaseConfigError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.web.static import StaticWebBuildCommand

from ....utils import create_wheel


@pytest.fixture
def build_command(dummy_console, tmp_path):
    command = StaticWebBuildCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command.tools.shutil = mock.MagicMock(spec_set=shutil)

    return command


def test_build_app_no_config(build_command, first_app_generated, tmp_path):
    """An app with no config.toml supplied by a wheel gets a basic config."""

    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    # Mock some wheels without a config.toml
    def mock_run(*args, **kwargs):
        if args[0][5] == "wheel":
            create_wheel(
                bundle_path / "www/static/wheels",
                "first_app",
                extra_content=[
                    ("dependency/static/style.css", "span { margin: 10px; }\n"),
                ],
            )
        elif args[0][5] == "pip":
            create_wheel(
                bundle_path / "www/static/wheels",
                "dependency",
                extra_content=[
                    ("dependency/static/style.css", "div { margin: 10px; }\n"),
                ],
            )
            create_wheel(
                bundle_path / "www/static/wheels",
                "other",
                extra_content=[
                    ("other/static/style.css", "div { padding: 10px; }\n"),
                ],
            )
        else:
            raise ValueError("Unknown command")

    build_command.tools.subprocess.run.side_effect = mock_run

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    # Build the web app.
    build_command.build_app(first_app_generated)

    # Pyscript.toml has been written with only the packages content
    with (bundle_path / "www/pyscript.toml").open("rb") as f:
        assert tomllib.load(f) == {
            "packages": [
                "/static/wheels/dependency-1.2.3-py3-none-any.whl",
                "/static/wheels/first_app-1.2.3-py3-none-any.whl",
                "/static/wheels/other-1.2.3-py3-none-any.whl",
            ],
        }


def test_build_app_multiple_config(build_command, first_app_generated, tmp_path):
    """An app with multiple config.toml supplied by wheels fails to build."""

    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    # Mock some wheels without a config.toml
    def mock_run(*args, **kwargs):
        if args[0][5] == "wheel":
            create_wheel(
                bundle_path / "www/static/wheels",
                "first_app",
                extra_content=[
                    ("dependency/static/style.css", "span { margin: 10px; }\n"),
                    (
                        "dependency/deploy/config.toml",
                        """
backend = "pyscript"

[pyscript]
version = "2024.11.1"
""",
                    ),
                ],
            )
        elif args[0][5] == "pip":
            create_wheel(
                bundle_path / "www/static/wheels",
                "dependency",
                extra_content=[
                    ("dependency/static/style.css", "div { margin: 10px; }\n"),
                    (
                        "dependency/deploy/config.toml",
                        """
backend = "pyscript"

[pyscript]
version = "2024.10.1"
""",
                    ),
                ],
            )
            create_wheel(
                bundle_path / "www/static/wheels",
                "other",
                extra_content=[
                    ("other/static/style.css", "div { padding: 10px; }\n"),
                ],
            )
        else:
            raise ValueError("Unknown command")

    build_command.tools.subprocess.run.side_effect = mock_run

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    # Build the web app.
    with pytest.raises(
        BriefcaseConfigError,
        match=r"Only one backend configuration file can be supplied.",
    ):
        build_command.build_app(first_app_generated)


def test_build_app_config_no_backend(build_command, first_app_generated, tmp_path):
    """An app cannot be built with a config.toml containing no "backend" value."""

    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    # Mock some wheels with a single config.toml containing no backend value.
    def mock_run(*args, **kwargs):
        if args[0][5] == "wheel":
            create_wheel(
                bundle_path / "www/static/wheels",
                "first_app",
                extra_content=[
                    ("dependency/static/style.css", "span { margin: 10px; }\n"),
                    ("dependency/deploy/config.toml", ""),
                ],
            )
        elif args[0][5] == "pip":
            create_wheel(
                bundle_path / "www/static/wheels",
                "dependency",
                extra_content=[
                    ("dependency/static/style.css", "div { margin: 10px; }\n"),
                ],
            )
            create_wheel(
                bundle_path / "www/static/wheels",
                "other",
                extra_content=[
                    ("other/static/style.css", "div { padding: 10px; }\n"),
                ],
            )
        else:
            raise ValueError("Unknown command")

    build_command.tools.subprocess.run.side_effect = mock_run

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    # Build the web app.
    with pytest.raises(
        BriefcaseConfigError,
        match=r"No backend was provided in config.toml file.",
    ):
        build_command.build_app(first_app_generated)


def test_build_app_config_backend_warning(build_command, first_app_generated, tmp_path, capsys):
    """Briefcase raises a warning if "backend" value is not pyscript."""

    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    # Mock some wheels with a single config.toml containing no backend value.
    def mock_run(*args, **kwargs):
        if args[0][5] == "wheel":
            create_wheel(
                bundle_path / "www/static/wheels",
                "first_app",
                extra_content=[
                    ("dependency/static/style.css", "span { margin: 10px; }\n"),
                    (
                        "dependency/deploy/config.toml",
                        """
backend = "something-else"
""",
                    ),
                ],
            )
        elif args[0][5] == "pip":
            create_wheel(
                bundle_path / "www/static/wheels",
                "dependency",
                extra_content=[
                    ("dependency/static/style.css", "div { margin: 10px; }\n"),
                ],
            )
            create_wheel(
                bundle_path / "www/static/wheels",
                "other",
                extra_content=[
                    ("other/static/style.css", "div { padding: 10px; }\n"),
                ],
            )
        else:
            raise ValueError("Unknown command")

    build_command.tools.subprocess.run.side_effect = mock_run

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    build_command.build_app(first_app_generated)

    # Capture output and assert warning present.
    captured = capsys.readouterr()
    assert (
        "Only 'pyscript' backend is currently supported for web static builds." in captured.out
    )

    # Check pyscript.toml was created and has correct packages.
    with (bundle_path / "www/pyscript.toml").open("rb") as f:
        assert tomllib.load(f) == {
            "packages": [
                "/static/wheels/dependency-1.2.3-py3-none-any.whl",
                "/static/wheels/first_app-1.2.3-py3-none-any.whl",
                "/static/wheels/other-1.2.3-py3-none-any.whl",
            ],
        }


def test_build_app_no_wheel_pyscript_toml(build_command, first_app_generated, tmp_path):
    """An app with no pyscript.toml supplied by a wheel gets a basic config."""

    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    # Mock some wheels without a pyscript.toml
    def mock_run(*args, **kwargs):
        if args[0][5] == "wheel":
            create_wheel(
                bundle_path / "www/static/wheels",
                "first_app",
                extra_content=[
                    ("dependency/static/style.css", "span { margin: 10px; }\n"),
                    (
                        "dependency/deploy/config.toml",
                        """
backend = "pyscript"

[pyscript]
version = "2024.11.1"
""",
                    ),
                ],
            )
        elif args[0][5] == "pip":
            create_wheel(
                bundle_path / "www/static/wheels",
                "dependency",
                extra_content=[
                    ("dependency/static/style.css", "div { margin: 10px; }\n"),
                ],
            )
            create_wheel(
                bundle_path / "www/static/wheels",
                "other",
                extra_content=[
                    ("other/static/style.css", "div { padding: 10px; }\n"),
                ],
            )
        else:
            raise ValueError("Unknown command")

    build_command.tools.subprocess.run.side_effect = mock_run

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    # Build the web app.
    build_command.build_app(first_app_generated)

    # Pyscript.toml has been written with only the packages content
    with (bundle_path / "www/pyscript.toml").open("rb") as f:
        assert tomllib.load(f) == {
            "packages": [
                "/static/wheels/dependency-1.2.3-py3-none-any.whl",
                "/static/wheels/first_app-1.2.3-py3-none-any.whl",
                "/static/wheels/other-1.2.3-py3-none-any.whl",
            ],
        }


def test_build_app_invalid_wheel_pyscript_toml(
    build_command, first_app_generated, tmp_path
):
    """An app with an invalid pyscript.toml raises an error."""

    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    # Invoking build will create wheels as a side effect.
    def mock_run(*args, **kwargs):
        if args[0][5] == "wheel":
            create_wheel(
                bundle_path / "www/static/wheels",
                "first_app",
                extra_content=[
                    ("dependency/static/style.css", "span { margin: 10px; }\n"),
                    (
                        "dependency/deploy/config.toml",
                        """
backend = "pyscript"

[pyscript]
version = "2024.11.1"
""",
                    ),
                    (
                        "dependency/deploy/pyscript.toml",
                        """
This is not valid toml.
""",
                    ),
                ],
            )
        elif args[0][5] == "pip":
            create_wheel(
                bundle_path / "www/static/wheels",
                "dependency",
                extra_content=[
                    ("dependency/static/style.css", "div { margin: 10px; }\n"),
                ],
            )
            create_wheel(
                bundle_path / "www/static/wheels",
                "other",
                extra_content=[
                    ("other/static/style.css", "div { padding: 10px; }\n"),
                ],
            )
        else:
            raise ValueError("Unknown command")

    build_command.tools.subprocess.run.side_effect = mock_run

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    # Building the web app raises an error
    with pytest.raises(
        BriefcaseConfigError,
        match=r"Briefcase configuration error: pyscript.toml content isn't valid TOML: Expected",
    ):
        build_command.build_app(first_app_generated)

