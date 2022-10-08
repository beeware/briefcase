import shutil
import subprocess
import sys
from unittest import mock

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.web.static import StaticWebBuildCommand

from ....utils import create_wheel


@pytest.fixture
def build_command(tmp_path):
    command = StaticWebBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command.tools.shutil = mock.MagicMock(spec_set=shutil)

    return command


def test_build_app(build_command, first_app_generated, tmp_path):
    "An app can be built"
    bundle_path = tmp_path / "base_path" / "web" / "static" / "First App"

    # Invoking build will create wheels as a side effect.
    def mock_run(*args, **kwargs):
        if args[0][3] == "wheel":
            create_wheel(
                bundle_path / "www" / "static" / "wheels",
                "first_app",
                extra_content=[
                    ("dependency/static/style.css", "span { margin: 10px; }\n"),
                ],
            ),
        elif args[0][3] == "pip":
            create_wheel(
                bundle_path / "www" / "static" / "wheels",
                "dependency",
                extra_content=[
                    ("dependency/static/style.css", "div { margin: 10px; }\n"),
                ],
            ),
            create_wheel(
                bundle_path / "www" / "static" / "wheels",
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
        bundle_path / "www" / "static" / "wheels"
    )

    # Build the web app.
    build_command.build_app(first_app_generated)

    # The old wheel folder was removed
    build_command.tools.shutil.rmtree.assert_called_once_with(
        bundle_path / "www" / "static" / "wheels"
    )

    # `wheel pack` and `pip wheel` was invoked
    assert build_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                sys.executable,
                "-u",
                "-m",
                "wheel",
                "pack",
                bundle_path / "app",
                "--dest-dir",
                bundle_path / "www" / "static" / "wheels",
            ],
            check=True,
        ),
        mock.call(
            [
                sys.executable,
                "-u",
                "-m",
                "pip",
                "wheel",
                "--wheel-dir",
                bundle_path / "www" / "static" / "wheels",
                "-r",
                bundle_path / "requirements.txt",
            ],
            check=True,
        ),
    ]

    # Pyscript.toml has been written
    with (bundle_path / "www" / "pyscript.toml").open("rb") as f:
        assert tomllib.load(f) == {
            "name": "First App",
            "description": "The first simple app \\ demonstration",
            "version": "0.0.1",
            "autoclose_loader": True,
            "packages": [
                "/static/wheels/dependency-1.2.3-py3-none-any.whl",
                "/static/wheels/first_app-1.2.3-py3-none-any.whl",
                "/static/wheels/other-1.2.3-py3-none-any.whl",
            ],
        }

    # briefcase.css has been appended
    with (bundle_path / "www" / "static" / "css" / "briefcase.css").open(
        encoding="utf-8"
    ) as f:
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


def test_build_app_missing_wheel_dir(build_command, first_app_generated, tmp_path):
    "If the template is corrupted, the wheels folder is still created."
    bundle_path = tmp_path / "base_path" / "web" / "static" / "First App"

    # Remove the wheels folder
    shutil.rmtree(bundle_path / "www" / "static" / "wheels")

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
                "-m",
                "wheel",
                "pack",
                bundle_path / "app",
                "--dest-dir",
                bundle_path / "www" / "static" / "wheels",
            ],
            check=True,
        ),
        mock.call(
            [
                sys.executable,
                "-u",
                "-m",
                "pip",
                "wheel",
                "--wheel-dir",
                bundle_path / "www" / "static" / "wheels",
                "-r",
                bundle_path / "requirements.txt",
            ],
            check=True,
        ),
    ]

    # Wheels folder exists
    assert (bundle_path / "www" / "static" / "wheels").is_dir()

    # Pyscript.toml has been written
    assert (bundle_path / "www" / "pyscript.toml").exists()

    # briefcase.css has been appended
    # (just check for existence; a full check is done in other tests)
    assert (bundle_path / "www" / "static" / "css" / "briefcase.css").exists()


def test_build_app_no_dependencies(build_command, first_app_generated, tmp_path):
    "An app with no dependencies can be built"
    bundle_path = tmp_path / "base_path" / "web" / "static" / "First App"

    # Invoking build will create wheels as a side effect.
    def mock_run(*args, **kwargs):
        if args[0][3] == "wheel":
            create_wheel(
                bundle_path / "www" / "static" / "wheels",
                "first_app",
                extra_content=[
                    ("dependency/static/style.css", "span { margin: 10px; }\n"),
                ],
            ),
        elif args[0][3] == "pip":
            pass
        else:
            raise ValueError("Unknown command")

    build_command.tools.subprocess.run.side_effect = mock_run

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www" / "static" / "wheels"
    )

    # Build the web app.
    build_command.build_app(first_app_generated)

    # The old wheel folder was removed
    build_command.tools.shutil.rmtree.assert_called_once_with(
        bundle_path / "www" / "static" / "wheels"
    )

    # `wheel pack` and `pip wheel` was invoked
    assert build_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                sys.executable,
                "-u",
                "-m",
                "wheel",
                "pack",
                bundle_path / "app",
                "--dest-dir",
                bundle_path / "www" / "static" / "wheels",
            ],
            check=True,
        ),
        mock.call(
            [
                sys.executable,
                "-u",
                "-m",
                "pip",
                "wheel",
                "--wheel-dir",
                bundle_path / "www" / "static" / "wheels",
                "-r",
                bundle_path / "requirements.txt",
            ],
            check=True,
        ),
    ]

    # Pyscript.toml has been written
    with (bundle_path / "www" / "pyscript.toml").open("rb") as f:
        assert tomllib.load(f) == {
            "name": "First App",
            "description": "The first simple app \\ demonstration",
            "version": "0.0.1",
            "autoclose_loader": True,
            "packages": [
                "/static/wheels/first_app-1.2.3-py3-none-any.whl",
            ],
        }

    # briefcase.css has been appended
    with (bundle_path / "www" / "static" / "css" / "briefcase.css").open(
        encoding="utf-8"
    ) as f:
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
    "If the app can't be packaged as a wheel,an error is raised."
    bundle_path = tmp_path / "base_path" / "web" / "static" / "First App"

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www" / "static" / "wheels"
    )

    # Mock the side effect of a successful package build, but failure
    # downloading dependencies
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
        bundle_path / "www" / "static" / "wheels"
    )

    # `wheel pack` was invoked
    assert build_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                sys.executable,
                "-u",
                "-m",
                "wheel",
                "pack",
                bundle_path / "app",
                "--dest-dir",
                bundle_path / "www" / "static" / "wheels",
            ],
            check=True,
        ),
    ]

    # Wheels folder still exists
    assert (bundle_path / "www" / "static" / "wheels").is_dir()

    # Pyscript.toml was not written
    assert not (bundle_path / "www" / "pyscript.toml").exists()


def test_dependency_fail(build_command, first_app_generated, tmp_path):
    "If dependnecies can't be downloaded, an error is raised."
    bundle_path = tmp_path / "base_path" / "web" / "static" / "First App"

    # Mock the side effect of invoking shutil
    build_command.tools.shutil.rmtree.side_effect = lambda *args: shutil.rmtree(
        bundle_path / "www" / "static" / "wheels"
    )

    # Mock the side effect of a successful package build, but failure
    # downloading dependencies
    build_command.tools.subprocess.run.side_effect = [
        None,
        subprocess.CalledProcessError(cmd=["pip", "wheel"], returncode=1),
    ]

    # Build the web app.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to install dependencies for app 'first-app'",
    ):
        build_command.build_app(first_app_generated)

    # The old wheel folder was removed
    build_command.tools.shutil.rmtree.assert_called_once_with(
        bundle_path / "www" / "static" / "wheels"
    )

    # `wheel pack` and `pip wheel` was invoked
    assert build_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                sys.executable,
                "-u",
                "-m",
                "wheel",
                "pack",
                bundle_path / "app",
                "--dest-dir",
                bundle_path / "www" / "static" / "wheels",
            ],
            check=True,
        ),
        mock.call(
            [
                sys.executable,
                "-u",
                "-m",
                "pip",
                "wheel",
                "--wheel-dir",
                bundle_path / "www" / "static" / "wheels",
                "-r",
                bundle_path / "requirements.txt",
            ],
            check=True,
        ),
    ]

    # Wheels folder still exists
    assert (bundle_path / "www" / "static" / "wheels").is_dir()

    # Pyscript.toml was not written
    assert not (bundle_path / "www" / "pyscript.toml").exists()
