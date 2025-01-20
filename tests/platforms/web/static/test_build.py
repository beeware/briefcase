import shutil
import subprocess
import sys
from unittest import mock

if sys.version_info >= (3, 11):  # pragma: no-cover-if-lt-py311
    import tomllib
else:  # pragma: no-cover-if-gte-py311
    import tomli as tomllib

import pytest

from briefcase.console import Console, LogLevel
from briefcase.exceptions import BriefcaseCommandError, BriefcaseConfigError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.web.static import StaticWebBuildCommand

from ....utils import create_file, create_wheel


@pytest.fixture
def build_command(tmp_path):
    command = StaticWebBuildCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command.tools.shutil = mock.MagicMock(spec_set=shutil)

    return command


@pytest.mark.parametrize("logging_level", [LogLevel.INFO, LogLevel.DEEP_DEBUG])
def test_build_app(build_command, first_app_generated, logging_level, tmp_path):
    """An app can be built."""
    # Configure logging level
    build_command.console.verbosity = logging_level

    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    # Invoking build will create wheels as a side effect.
    def mock_run(*args, **kwargs):
        if args[0][5] == "wheel":
            create_wheel(
                bundle_path / "www/static/wheels",
                "first_app",
                extra_content=[
                    ("dependency/static/style.css", "span { margin: 10px; }\n"),
                ],
            ),
        elif args[0][5] == "pip":
            create_wheel(
                bundle_path / "www/static/wheels",
                "dependency",
                extra_content=[
                    ("dependency/static/style.css", "div { margin: 10px; }\n"),
                ],
            ),
            create_wheel(
                bundle_path / "www/static/wheels",
                "other",
                extra_content=[
                    ("other/static/style.css", "div { padding: 10px; }\n"),
                ],
            ),
        else:
            raise ValueError("Unknown command")

    build_command.tools.subprocess.run.side_effect = mock_run

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    # Build the web app.
    build_command.build_app(first_app_generated)

    # The old wheel folder was removed
    build_command.tools.shutil.rmtree.assert_called_once_with(
        bundle_path / "www/static/wheels"
    )

    # `wheel pack` and `pip wheel` was invoked
    assert build_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "wheel",
                "pack",
                bundle_path / "app",
                "--dest-dir",
                bundle_path / "www/static/wheels",
            ],
            check=True,
            encoding="UTF-8",
        ),
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "wheel",
                "--wheel-dir",
                bundle_path / "www/static/wheels",
                "-r",
                bundle_path / "requirements.txt",
            ]
            + (["-vv"] if logging_level == LogLevel.DEEP_DEBUG else []),
            check=True,
            encoding="UTF-8",
        ),
    ]

    # Pyscript.toml has been written
    with (bundle_path / "www/pyscript.toml").open("rb") as f:
        assert tomllib.load(f) == {
            "existing-key-1": "value-1",
            "existing-key-2": 2,
            "packages": [
                "/static/wheels/dependency-1.2.3-py3-none-any.whl",
                "/static/wheels/first_app-1.2.3-py3-none-any.whl",
                "/static/wheels/other-1.2.3-py3-none-any.whl",
            ],
        }

    # briefcase.css has been appended
    with (bundle_path / "www/static/css/briefcase.css").open(encoding="utf-8") as f:
        assert (
            f.read()
            == "\n".join(
                [
                    "",
                    "#pyconsole {",
                    "  display: None;",
                    "}",
                    "/*******************************************************************",
                    " ******************** Wheel contributed styles ********************/",
                    "",
                    "/*******************************************************",
                    " * dependency 1.2.3::style.css",
                    " *******************************************************/",
                    "",
                    "div { margin: 10px; }",
                    "",
                    "/*******************************************************",
                    " * first_app 1.2.3::style.css",
                    " *******************************************************/",
                    "",
                    "span { margin: 10px; }",
                    "",
                    "/*******************************************************",
                    " * other 1.2.3::style.css",
                    " *******************************************************/",
                    "",
                    "div { padding: 10px; }",
                ]
            )
            + "\n"
        )


def test_build_app_custom_pyscript_toml(build_command, first_app_generated, tmp_path):
    """An app with extra pyscript.toml content can be written."""
    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    first_app_generated.extra_pyscript_toml_content = (
        "\n".join(
            [
                # A custom top level key
                'something = "custom"',
                # A key overwriting something in the main namespace
                'packages = ["something-custom"]',
                # A table overwriting an existing value
                "[splashscreen]",
                "wiggle = false",
                # A custom array of tables
                "[[runtimes]]",
                'src = "https://example.com/pyodide.js"',
            ]
        )
        + "\n"
    )

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    # Build the web app.
    build_command.build_app(first_app_generated)

    # Pyscript.toml has been written
    with (bundle_path / "www/pyscript.toml").open("rb") as f:
        assert tomllib.load(f) == {
            "existing-key-1": "value-1",
            "existing-key-2": 2,
            "something": "custom",
            "splashscreen": {"wiggle": False},
            "packages": ["something-custom"],
            "runtimes": [
                {"src": "https://example.com/pyodide.js"},
            ],
        }


def test_build_app_no_template_pyscript_toml(
    build_command, first_app_generated, tmp_path
):
    """An app whose template doesn't provide pyscript.toml gets a basic config."""
    # Remove the templated pyscript.toml
    bundle_path = tmp_path / "base_path/build/first-app/web/static"
    (bundle_path / "www/pyscript.toml").unlink()

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    # Build the web app.
    build_command.build_app(first_app_generated)

    # Pyscript.toml has been written with only the packages content
    with (bundle_path / "www/pyscript.toml").open("rb") as f:
        assert tomllib.load(f) == {
            "packages": [],
        }


def test_build_app_invalid_template_pyscript_toml(
    build_command, first_app_generated, tmp_path
):
    """An app with an invalid pyscript.toml raises an error."""
    # Re-write an invalid templated pyscript.toml
    bundle_path = tmp_path / "base_path/build/first-app/web/static"
    (bundle_path / "www/pyscript.toml").unlink()
    create_file(
        bundle_path / "www/pyscript.toml",
        """
This is not valid toml.
""",
    )

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


def test_build_app_invalid_extra_pyscript_toml_content(
    build_command, first_app_generated, tmp_path
):
    """An app with invalid extra pyscript.toml content raises an error."""
    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    first_app_generated.extra_pyscript_toml_content = "This isn't toml"

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    # Building the web app raises an error
    with pytest.raises(
        BriefcaseConfigError,
        match=r"Briefcase configuration error: Extra pyscript.toml content isn't valid TOML: Expected",
    ):
        build_command.build_app(first_app_generated)


def test_build_app_missing_wheel_dir(build_command, first_app_generated, tmp_path):
    """If the template is corrupted, the wheels folder is still created."""
    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    # Remove the wheels folder
    shutil.rmtree(bundle_path / "www/static/wheels")

    # Build the web app.
    build_command.build_app(first_app_generated)

    # No attempt was made to delete the folder
    build_command.tools.shutil.rmtree.assert_not_called()

    # `wheel pack` and `pip wheel` was invoked
    assert build_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "wheel",
                "pack",
                bundle_path / "app",
                "--dest-dir",
                bundle_path / "www/static/wheels",
            ],
            check=True,
            encoding="UTF-8",
        ),
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "wheel",
                "--wheel-dir",
                bundle_path / "www/static/wheels",
                "-r",
                bundle_path / "requirements.txt",
            ],
            check=True,
            encoding="UTF-8",
        ),
    ]

    # Wheels folder exists
    assert (bundle_path / "www/static/wheels").is_dir()

    # Pyscript.toml has been written
    assert (bundle_path / "www/pyscript.toml").exists()

    # briefcase.css has been appended
    # (just check for existence; a full check is done in other tests)
    assert (bundle_path / "www/static/css/briefcase.css").exists()


def test_build_app_no_requirements(build_command, first_app_generated, tmp_path):
    """An app with no requirements can be built."""
    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    # Invoking build will create wheels as a side effect.
    def mock_run(*args, **kwargs):
        if args[0][5] == "wheel":
            create_wheel(
                bundle_path / "www/static/wheels",
                "first_app",
                extra_content=[
                    ("dependency/static/style.css", "span { margin: 10px; }\n"),
                ],
            ),
        elif args[0][5] == "pip":
            pass
        else:
            raise ValueError("Unknown command")

    build_command.tools.subprocess.run.side_effect = mock_run

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    # Build the web app.
    build_command.build_app(first_app_generated)

    # The old wheel folder was removed
    build_command.tools.shutil.rmtree.assert_called_once_with(
        bundle_path / "www/static/wheels"
    )

    # `wheel pack` and `pip wheel` was invoked
    assert build_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "wheel",
                "pack",
                bundle_path / "app",
                "--dest-dir",
                bundle_path / "www/static/wheels",
            ],
            check=True,
            encoding="UTF-8",
        ),
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "wheel",
                "--wheel-dir",
                bundle_path / "www/static/wheels",
                "-r",
                bundle_path / "requirements.txt",
            ],
            check=True,
            encoding="UTF-8",
        ),
    ]

    # Pyscript.toml has been written
    with (bundle_path / "www/pyscript.toml").open("rb") as f:
        assert tomllib.load(f) == {
            "existing-key-1": "value-1",
            "existing-key-2": 2,
            "packages": [
                "/static/wheels/first_app-1.2.3-py3-none-any.whl",
            ],
        }

    # briefcase.css has been appended
    with (bundle_path / "www/static/css/briefcase.css").open(encoding="utf-8") as f:
        assert (
            f.read()
            == "\n".join(
                [
                    "",
                    "#pyconsole {",
                    "  display: None;",
                    "}",
                    "/*******************************************************************",
                    " ******************** Wheel contributed styles ********************/",
                    "",
                    "/*******************************************************",
                    " * first_app 1.2.3::style.css",
                    " *******************************************************/",
                    "",
                    "span { margin: 10px; }",
                ]
            )
            + "\n"
        )


def test_app_package_fail(build_command, first_app_generated, tmp_path):
    """If the app can't be packaged as a wheel,an error is raised."""
    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    # Mock the side effect of a successful package build, but failure
    # downloading requirements
    build_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(cmd=["wheel"], returncode=1),
    ]

    # Build the web app.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to build wheel for app 'first-app'",
    ):
        build_command.build_app(first_app_generated)

    # The old wheel folder was removed
    build_command.tools.shutil.rmtree.assert_called_once_with(
        bundle_path / "www/static/wheels"
    )

    # `wheel pack` was invoked
    assert build_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "wheel",
                "pack",
                bundle_path / "app",
                "--dest-dir",
                bundle_path / "www/static/wheels",
            ],
            check=True,
            encoding="UTF-8",
        ),
    ]

    # Wheels folder still exists
    assert (bundle_path / "www/static/wheels").is_dir()

    # Pyscript.toml content has not changed
    with (bundle_path / "www/pyscript.toml").open("rb") as f:
        assert tomllib.load(f) == {
            "existing-key-1": "value-1",
            "existing-key-2": 2,
        }


def test_dependency_fail(build_command, first_app_generated, tmp_path):
    """If dependencies can't be downloaded, an error is raised."""
    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www/static/wheels"
    )

    # Mock the side effect of a successful package build, but failure
    # downloading requirements
    build_command.tools.subprocess.run.side_effect = [
        None,
        subprocess.CalledProcessError(cmd=["pip", "wheel"], returncode=1),
    ]

    # Build the web app.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to install requirements for app 'first-app'",
    ):
        build_command.build_app(first_app_generated)

    # The old wheel folder was removed
    build_command.tools.shutil.rmtree.assert_called_once_with(
        bundle_path / "www/static/wheels"
    )

    # `wheel pack` and `pip wheel` was invoked
    assert build_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "wheel",
                "pack",
                bundle_path / "app",
                "--dest-dir",
                bundle_path / "www/static/wheels",
            ],
            check=True,
            encoding="UTF-8",
        ),
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "wheel",
                "--wheel-dir",
                bundle_path / "www/static/wheels",
                "-r",
                bundle_path / "requirements.txt",
            ],
            check=True,
            encoding="UTF-8",
        ),
    ]

    # Wheels folder still exists
    assert (bundle_path / "www/static/wheels").is_dir()

    # Pyscript.toml content has not changed
    with (bundle_path / "www/pyscript.toml").open("rb") as f:
        assert tomllib.load(f) == {
            "existing-key-1": "value-1",
            "existing-key-2": 2,
        }
