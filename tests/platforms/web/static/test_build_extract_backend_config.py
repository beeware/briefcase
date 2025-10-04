import shutil
import subprocess
import sys
from unittest import mock

if sys.version_info >= (3, 11):  # pragma: no-cover-if-lt-py311
    import tomllib
else:  # pragma: no-cover-if-gte-py311
    import tomli as tomllib

import pytest
from zipfile import ZipFile
import tomllib
import io

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

def _mock_wheel(tmp_path, wheel_name, files):
    """Function to mock wheel files in tests."""
    wheel_path = tmp_path / wheel_name
    with ZipFile(wheel_path, "w") as wheel:
        for filename, content in files.items():
            wheel.writestr(filename, content)
    return wheel_path


def test_extract_backend_config(build_command, tmp_path):
    """Test function works correctly with both config.toml and pyscript.toml."""
    # Mock a wheel with files
    files = {
        "dependancy/deploy/config.toml": """
backend = "pyscript"

[pyscript]
version = "2024.10.1"
""",
        "dependancy/deploy/pyscript.toml": """
existing-key-1 = "value-1"
existing-key-2 = 2
""",
    }

    wheel_path = _mock_wheel(tmp_path=tmp_path, wheel_name="dependancy", files=files)

    # Run the function.
    pyscript_config, pyscript_version = build_command.extract_backend_config([wheel_path])

    # Check returns are correct and files were found.
    assert pyscript_config == {
        "existing-key-1": "value-1",
        "existing-key-2": 2,
    }
    assert pyscript_version == "2024.10.1"


def test_extract_backend_config_no_config(build_command, tmp_path):
    """If no config.toml supplied by wheels, functions returns a basic config."""
    # Mock a wheel without the needed files
    files = {
        "dependancy/deploy/not-the-files-you-are-looking-for.toml": ""
    }

    wheel_path = _mock_wheel(tmp_path=tmp_path, wheel_name="dependancy", files=files)

    # Run the function.
    pyscript_config, pyscript_version = build_command.extract_backend_config([wheel_path])

    # Check pyscript_config is empty and pyscript_version is the default.
    assert pyscript_config == {}
    assert pyscript_version == "2024.11.1"


def test_extract_backend_config_multiple_config(build_command, tmp_path):
    """Multiple config.toml supplied by wheels fails."""

    # Mock wheels that both contain config.toml
    file_set_1 = {
        "dependancy/deploy/config.toml": """
backend = "pyscript"

[pyscript]
version = "2024.10.1"
""",
    }

    file_set_2 = {
        "dependancy/deploy/config.toml": """
backend = "pyscript"

[pyscript]
version = "2024.10.1"
""",
    }

    wheel_path_1 = _mock_wheel(tmp_path=tmp_path, wheel_name="dependancy", files=file_set_1)
    wheel_path_2 = _mock_wheel(tmp_path=tmp_path, wheel_name="dependancy", files=file_set_2)

    # Run the function.
    with pytest.raises(
        BriefcaseConfigError,
        match=r"Only one backend configuration file can be supplied.",
    ):
        build_command.extract_backend_config([wheel_path_1, wheel_path_2])


def test_extract_backend_config_no_backend(build_command, tmp_path):
    """An app cannot be built with a config.toml containing no "backend" value."""

    # Mock a wheel with the needed files
    files = {
        "dependancy/deploy/config.toml": ""
    }

    wheel_path = _mock_wheel(tmp_path=tmp_path, wheel_name="dependancy", files=files)

    # Build the web app.
    with pytest.raises(
        BriefcaseConfigError,
        match=r"No backend was provided in config.toml file.",
    ):
        build_command.extract_backend_config([wheel_path])


def test_extract_backend_config_backend_warning(build_command, tmp_path, capsys):
    """Briefcase raises a warning if "backend" value is not pyscript."""

    files = {
        "dependancy/deploy/config.toml": """
backend = "something-else"
""",
}

    wheel_path = _mock_wheel(tmp_path=tmp_path, wheel_name="dependancy", files=files)

    pyscript_config, pyscript_version = build_command.extract_backend_config([wheel_path])

    # Capture output and assert warning present.
    captured = capsys.readouterr()
    assert (
        "Only 'pyscript' backend is currently supported for web static builds." in captured.out
    )

    # Check pyscript_config is empty and pyscript_version is the default.
    assert pyscript_config == {}
    assert pyscript_version == "2024.11.1"


def test_extract_backend_config_no_pyscript_toml(build_command, tmp_path):
    """If no pyscript.toml is supplied by a wheel, function returns a basic config."""

    # Create wheel with no pyscript.toml
    files = {
        "dependancy/deploy/config.toml": """
backend = "pyscript"
""",
}

    wheel_path = _mock_wheel(tmp_path=tmp_path, wheel_name="dependancy", files=files)

    pyscript_config, pyscript_version = build_command.extract_backend_config([wheel_path])

    # Check pyscript_config is empty and pyscript_version is the default.
    assert pyscript_config == {}
    assert pyscript_version == "2024.11.1"


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

