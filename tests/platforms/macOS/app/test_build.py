from unittest import mock

import pytest

from briefcase.console import Console
from briefcase.platforms.macOS import SigningIdentity
from briefcase.platforms.macOS.app import macOSAppBuildCommand


@pytest.fixture
def build_command(tmp_path):
    command = macOSAppBuildCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    command.select_identity = mock.MagicMock()
    command.sign_app = mock.MagicMock()
    command.sign_file = mock.MagicMock()

    return command


@pytest.mark.parametrize("universal_build", [True, False])
@pytest.mark.parametrize("pre_existing", [True, False])
@pytest.mark.parametrize("console_app", [True, False])
def test_build_app(
    build_command,
    first_app_with_binaries,
    console_app,
    universal_build,
    pre_existing,
    tmp_path,
):
    """A macOS App is ad-hoc signed as part of the build process."""
    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    first_app_with_binaries.universal_build = universal_build
    first_app_with_binaries.console_app = console_app
    build_command.tools.host_arch = "gothic"

    exec_path = bundle_path / "First App.app/Contents/MacOS"
    if not pre_existing:
        # If this not a pre-existing app, the stub has the original name
        (exec_path / "First App").rename(exec_path / "Stub")

    # Mock the thin command so we can confirm if it was invoked.
    build_command.ensure_thin_binary = mock.Mock()

    # Build the app
    build_command.build_app(first_app_with_binaries, test_mode=False)

    # The stub binary has been renamed
    assert not (exec_path / "Stub").is_file()
    assert (exec_path / "First App").is_file()

    # Only thin if this is a non-universal app
    if universal_build:
        build_command.ensure_thin_binary.assert_not_called()
    else:
        build_command.ensure_thin_binary.assert_called_once_with(
            exec_path / "First App",
            arch="gothic",
        )

    # A request has been made to sign the app
    build_command.sign_app.assert_called_once_with(
        app=first_app_with_binaries,
        identity=SigningIdentity(),
    )

    # No request to select a signing identity was made
    build_command.select_identity.assert_not_called()

    # No attempt was made to sign a specific file;
    # This ignores the calls that would have been made transitively
    # by calling sign_app()
    build_command.sign_file.assert_not_called()
