import shutil
import sys
from unittest import mock

if sys.version_info >= (3, 11):  # pragma: no-cover-if-lt-py311
    pass
else:  # pragma: no-cover-if-gte-py311
    pass

from zipfile import ZipFile

import pytest

from briefcase.exceptions import BriefcaseConfigError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.web.static import StaticWebBuildCommand


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


def test_extract_pyscript_config(build_command, tmp_path):
    """Test function works correctly with both config.toml and pyscript.toml."""
    # Mock a wheel with files
    files = {
        "dependency/deploy/config.toml": """
implementation = "pyscript"

[pyscript]
version = "2024.10.1"
""",
        "dependency/deploy/pyscript.toml": """
existing-key-1 = "value-1"
existing-key-2 = 2
""",
    }

    wheel_path = _mock_wheel(tmp_path=tmp_path, wheel_name="dependency", files=files)

    # Run the function.
    pyscript_config, pyscript_version = build_command.extract_pyscript_config(
        [wheel_path]
    )

    # Check returns are correct and files were found.
    assert pyscript_config == {
        "existing-key-1": "value-1",
        "existing-key-2": 2,
    }
    assert pyscript_version == "2024.10.1"


def test_extract_pyscript_config_no_config(build_command, tmp_path):
    """If no config.toml supplied by wheels, functions returns a basic config."""
    # Mock a wheel without the needed files
    files = {"dependency/deploy/not-the-files-you-are-looking-for.toml": ""}

    wheel_path = _mock_wheel(tmp_path=tmp_path, wheel_name="dependency", files=files)

    # Run the function.
    pyscript_config, pyscript_version = build_command.extract_pyscript_config(
        [wheel_path]
    )

    # Check pyscript_config is empty and pyscript_version is the default.
    assert pyscript_config == {}
    assert pyscript_version == "2024.11.1"


def test_extract_pyscript_config_multiple_config(build_command, tmp_path):
    """Multiple config.toml supplied by wheels fails."""

    # Mock wheels that both contain config.toml
    file_set_1 = {
        "dependency/deploy/config.toml": """
implementation = "pyscript"

[pyscript]
version = "2024.10.1"
""",
    }

    file_set_2 = {
        "dependency/deploy/config.toml": """
implementation = "pyscript"

[pyscript]
version = "2024.10.1"
""",
    }

    wheel_path_1 = _mock_wheel(
        tmp_path=tmp_path, wheel_name="dependency", files=file_set_1
    )
    wheel_path_2 = _mock_wheel(
        tmp_path=tmp_path, wheel_name="dependency", files=file_set_2
    )

    # Run the function.
    with pytest.raises(
        BriefcaseConfigError,
        match=r"Only one deployment configuration file can be supplied.",
    ):
        build_command.extract_pyscript_config([wheel_path_1, wheel_path_2])


def test_extract_pyscript_config_no_implementation(build_command, tmp_path, capsys):
    """An app with no "implementation" value defaults to pyscript with a warning."""

    # Mock a wheel with the needed files
    files = {"dependency/deploy/config.toml": ""}

    wheel_path = _mock_wheel(tmp_path=tmp_path, wheel_name="dependency", files=files)

    pyscript_config, pyscript_version = build_command.extract_pyscript_config(
        [wheel_path]
    )

    # Capture output and assert warning present.
    captured = capsys.readouterr()
    assert "No web implementation specified. Defaulting to 'pyscript'." in captured.out

    # Check pyscript_config is empty and pyscript_version is the default.
    assert pyscript_config == {}
    assert pyscript_version == "2024.11.1"


def test_extract_pyscript_config_implementation_warning(
    build_command,
    tmp_path,
    capsys,
):
    """Briefcase raises a warning if "implementation" value is not pyscript."""

    files = {
        "dependency/deploy/config.toml": """
implementation = "something-else"
""",
    }

    wheel_path = _mock_wheel(tmp_path=tmp_path, wheel_name="dependency", files=files)

    pyscript_config, pyscript_version = build_command.extract_pyscript_config(
        [wheel_path]
    )

    # Capture output and assert warning present.
    captured = capsys.readouterr()
    assert (
        "At present, 'pyscript' is the only supported web implementation."
        in captured.out
    )

    # Check pyscript_config is empty and pyscript_version is the default.
    assert pyscript_config == {}
    assert pyscript_version == "2024.11.1"


def test_extract_pyscript_config_no_pyscript_toml(build_command, tmp_path, capsys):
    """If no pyscript.toml is supplied by a wheel, function returns a basic config."""

    # Create wheel with no pyscript.toml
    files = {
        "dependency/deploy/config.toml": """
implementation = "pyscript"
""",
    }

    wheel_path = _mock_wheel(tmp_path=tmp_path, wheel_name="dependency", files=files)

    pyscript_config, pyscript_version = build_command.extract_pyscript_config(
        [wheel_path]
    )
    # Capture output and assert console info is present.
    captured = capsys.readouterr()
    assert "Pyscript configuration file not found in" in captured.out

    # Check pyscript_config is empty and pyscript_version is the default.
    assert pyscript_config == {}
    assert pyscript_version == "2024.11.1"


def test_extract_pyscript_config_invalid_wheel_pyscript_toml(build_command, tmp_path):
    """A wheel with an invalid pyscript.toml raises an error."""

    # Mock a wheel with files
    files = {
        "dependency/deploy/config.toml": """
implementation = "pyscript"

[pyscript]
version = "2024.10.1"
""",
        "dependency/deploy/pyscript.toml": """
This is not valid toml.
""",
    }

    wheel_path = _mock_wheel(tmp_path=tmp_path, wheel_name="dependency", files=files)

    # Building the web app raises an error
    with pytest.raises(
        BriefcaseConfigError,
        match=r"Briefcase configuration error: pyscript.toml content isn't valid TOML: Expected",
    ):
        build_command.extract_pyscript_config([wheel_path])
