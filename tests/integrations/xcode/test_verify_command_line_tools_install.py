from subprocess import CalledProcessError
from unittest import mock

from briefcase.integrations.xcode import verify_command_line_tools_install


def test_verify_command_line_tools_install(mock_tools):
    "Xcode CLI tools can be verified"
    mock_tools.subprocess.check_output.side_effect = [
        CalledProcessError(cmd=["xcode-select", "--install"], returncode=1),
        "clang 37.42",  # clang --version
    ]

    verify_command_line_tools_install(mock_tools)

    # The command line tools are verified
    assert mock_tools.xcode_cli is not None


def test_reverify_command_line_tools_install(mock_tools):
    "A second call to verify is a no-op"

    xcode_cli = mock.MagicMock()
    mock_tools.xcode_cli = xcode_cli

    verify_command_line_tools_install(mock_tools)

    # The command line tools are verified
    assert mock_tools.xcode_cli is not None
