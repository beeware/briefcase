from subprocess import CalledProcessError
from unittest import mock

from briefcase.integrations.xcode import verify_xcode_install


def test_verify_xcode_install(mock_tools):
    "Xcode can be verified"
    mock_tools.subprocess.check_output.side_effect = [
        "/Applications/Xcode/app/Contents/Developer",  # xcode-select -p
        "Xcode 14.0.1",  # xcodebuild -version
        CalledProcessError(cmd=["xcode-select", "--install"], returncode=1),
        "clang 37.42",  # clang --version
    ]

    verify_xcode_install(mock_tools)

    # Both Xcode and the command line tools are verified
    assert mock_tools.xcode is not None
    assert mock_tools.xcode_cli is not None


def test_reverify_xcode_install(mock_tools):
    "A second call to verify is a no-op"

    xcode = mock.MagicMock()
    mock_tools.xcode = xcode

    xcode_cli = mock.MagicMock()
    mock_tools.xcode_cli = xcode_cli

    verify_xcode_install(mock_tools)

    # Both Xcode and the command line tools are verified
    assert mock_tools.xcode == xcode
    assert mock_tools.xcode_cli is not None
