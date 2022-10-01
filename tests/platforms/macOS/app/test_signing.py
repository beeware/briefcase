import os
import subprocess
from unittest import mock

import pytest

from briefcase.commands.base import BaseCommand
from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS import macOSSigningMixin
from briefcase.platforms.macOS.app import macOSAppMixin
from tests.utils import DummyConsole


class DummySigningCommand(macOSAppMixin, macOSSigningMixin, BaseCommand):
    """A dummy command to expose code signing capabilities."""

    command = "sign"

    def __init__(self, base_path, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(base_path=base_path / "base_path", **kwargs)
        self.tools.input = DummyConsole()


@pytest.fixture
def dummy_command(tmp_path):
    cmd = DummySigningCommand(base_path=tmp_path)

    # Mock the options object
    cmd.options = mock.MagicMock()
    cmd.options.device = None

    # Mock get_identities
    mock_get_identities = mock.MagicMock()
    cmd.get_identities = mock_get_identities

    cmd.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    return cmd


def sign_call(
    tmp_path,
    filepath,
    identity="Sekrit identity (DEADBEEF)",
    entitlements=True,
    runtime=True,
    deep=False,
):
    """A test utility method to quickly construct a subprocess call to invoke
    codesign on a file."""
    args = [
        "codesign",
        os.fsdecode(filepath),
        "--sign",
        identity,
        "--force",
    ]
    if entitlements:
        args.extend(
            [
                "--entitlements",
                os.fsdecode(
                    tmp_path
                    / "base_path"
                    / "macOS"
                    / "app"
                    / "First App"
                    / "Entitlements.plist"
                ),
            ]
        )
    if runtime:
        args.extend(
            [
                "--options",
                "runtime",
            ]
        )
    if deep:
        args.append("--deep")

    return mock.call(args, stderr=subprocess.PIPE, check=True)


def mock_codesign(results):
    """A utility method for generating codesign side effects.

    :param results: A single error string; or a list of error strings to be returned
        on successive calls. If `None` is included in the list of results, no
        error will be raised for that invocation.
    """

    def _codesign(args, **kwargs):
        if isinstance(results, list):
            result = results.pop(0)
        else:
            result = results

        if result:
            raise subprocess.CalledProcessError(
                returncode=1, cmd=args, stderr=f"{args[1]}: {result}"
            )

    return _codesign


def test_explicit_identity_checksum(dummy_command):
    """If the user nominates an identity by checksum, it is used."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corporation Ltd (Z2K4383DLE)",
        "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # The identity will be the one the user specified as an option.
    result = dummy_command.select_identity("11E77FB58F13F6108B38110D5D92233C58ED38C5")

    assert result == (
        "11E77FB58F13F6108B38110D5D92233C58ED38C5",
        "iPhone Developer: Jane Smith (BXAH5H869S)",
    )

    # User input was not solicited
    assert dummy_command.input.prompts == []


def test_explicit_identity_name(dummy_command):
    """If the user nominates an identity by name, it is used."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corporation Ltd (Z2K4383DLE)",
        "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # The identity will be the one the user specified as an option.
    result = dummy_command.select_identity("iPhone Developer: Jane Smith (BXAH5H869S)")

    assert result == (
        "11E77FB58F13F6108B38110D5D92233C58ED38C5",
        "iPhone Developer: Jane Smith (BXAH5H869S)",
    )

    # User input was not solicited
    assert dummy_command.input.prompts == []


def test_invalid_identity_name(dummy_command):
    """If the user nominates an identity by name, it is used."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corporation Ltd (Z2K4383DLE)",
        "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # The identity will be the one the user specified as an option.
    with pytest.raises(BriefcaseCommandError):
        dummy_command.select_identity("not-an-identity")

    # User input was not solicited
    assert dummy_command.input.prompts == []


def test_implied_identity(dummy_command):
    """If there is only one identity, it is automatically picked."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    result = dummy_command.select_identity()

    # The identity will be the only option available.
    assert result == (
        "11E77FB58F13F6108B38110D5D92233C58ED38C5",
        "iPhone Developer: Jane Smith (BXAH5H869S)",
    )

    # User input was not solicited
    assert dummy_command.input.prompts == []


def test_no_identities(dummy_command):
    """If there are no identities an error is raised."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {}

    with pytest.raises(
        BriefcaseCommandError,
        match=r"No code signing identities are available.",
    ):
        dummy_command.select_identity()


def test_selected_identity(dummy_command):
    """If there is only one identity, it is automatically picked."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corporation Ltd (Z2K4383DLE)",
        "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # Return option 2
    dummy_command.input.values = ["2"]

    result = dummy_command.select_identity()

    # The identity will be the only option available.
    assert result == (
        "11E77FB58F13F6108B38110D5D92233C58ED38C5",
        "iPhone Developer: Jane Smith (BXAH5H869S)",
    )

    # User input was solicited once
    assert dummy_command.input.prompts == ["> "]


def test_sign_file_adhoc_identity(dummy_command, tmp_path):
    """If an adhoc identity is used, the runtime option isn't used."""
    # Sign the file with an adhoc identity
    dummy_command.sign_file(tmp_path / "base_path" / "random.file", identity="-")

    # An attempt to codesign was made without the runtime option
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(
                tmp_path,
                tmp_path / "base_path" / "random.file",
                identity="-",
                entitlements=False,
                runtime=False,
            ),
        ],
        any_order=False,
    )


def test_sign_file_entitlements(dummy_command, tmp_path):
    """Entitlements can be included in a signing call."""
    # Sign the file with an adhoc identity
    dummy_command.sign_file(
        tmp_path / "base_path" / "random.file",
        identity="Sekrit identity (DEADBEEF)",
        entitlements=tmp_path
        / "base_path"
        / "macOS"
        / "app"
        / "First App"
        / "Entitlements.plist",
    )

    # An attempt to codesign was made without the runtime option
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(tmp_path, tmp_path / "base_path" / "random.file"),
        ],
        any_order=False,
    )


def test_sign_file_deep_sign(dummy_command, tmp_path, capsys):
    """A file can be identified as needing a deep sign."""
    # First call raises the deep sign warning; second call succeeds
    dummy_command.tools.subprocess.run.side_effect = mock_codesign(
        [" code object is not signed at all", None]
    )

    # Sign the file
    dummy_command.sign_file(
        tmp_path / "base_path" / "random.file", identity="Sekrit identity (DEADBEEF)"
    )

    # 2 attempt to codesign was made; the second enabled the deep argument.
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(
                tmp_path,
                tmp_path / "base_path" / "random.file",
                entitlements=False,
            ),
            sign_call(
                tmp_path,
                tmp_path / "base_path" / "random.file",
                entitlements=False,
                deep=True,
            ),
        ],
        any_order=False,
    )

    # The console includes a warning about the attempt to deep sign
    assert "... file requires a deep sign; retrying\n" in capsys.readouterr().out


def test_sign_file_deep_sign_failure(dummy_command, tmp_path, capsys):
    """If deep signing fails, an error is raised."""
    # First invocation raises the deep sign error; second invocation raises some other error
    dummy_command.tools.subprocess.run.side_effect = mock_codesign(
        [
            " code object is not signed at all",
            " something went wrong!",
        ]
    )

    # Sign the file
    with pytest.raises(BriefcaseCommandError, match="Unable to deep code sign "):
        dummy_command.sign_file(
            tmp_path / "base_path" / "random.file",
            identity="Sekrit identity (DEADBEEF)",
        )

    # An attempt to codesign was made
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(
                tmp_path,
                tmp_path / "base_path" / "random.file",
                entitlements=False,
            ),
        ],
        any_order=False,
    )

    # The console includes a warning about the attempt to deep sign
    assert "... file requires a deep sign; retrying\n" in capsys.readouterr().out


def test_sign_file_unsupported_format(dummy_command, tmp_path, capsys):
    """If codesign reports an unsupported format, the signing attempt is
    ignored with a warning."""
    # FIXME: I'm not sure how to manufacture this in practice.
    dummy_command.tools.subprocess.run.side_effect = mock_codesign(
        "unsupported format for signature"
    )

    # Sign the file
    dummy_command.sign_file(
        tmp_path / "base_path" / "random.file",
        identity="Sekrit identity (DEADBEEF)",
    )

    # An attempt to codesign was made
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(
                tmp_path,
                tmp_path / "base_path" / "random.file",
                entitlements=False,
            ),
        ],
        any_order=False,
    )

    # The console includes a warning about not needing a signature.
    assert "... no signature required\n" in capsys.readouterr().out


def test_sign_file_unknown_bundle_format(dummy_command, tmp_path, capsys):
    """If a folder happens to have a .framework extension, the signing attempt
    is ignored with a warning."""
    # Raise an error caused by an unknown bundle format during codesign
    dummy_command.tools.subprocess.run.side_effect = mock_codesign(
        "bundle format unrecognized, invalid, or unsuitable"
    )

    # Sign the file
    dummy_command.sign_file(
        tmp_path / "base_path" / "random.file",
        identity="Sekrit identity (DEADBEEF)",
    )

    # An attempt to codesign was made
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(
                tmp_path,
                tmp_path / "base_path" / "random.file",
                entitlements=False,
            ),
        ],
        any_order=False,
    )

    # The console includes a warning about not needing a signature.
    assert "... no signature required\n" in capsys.readouterr().out


def test_sign_file_unknown_error(dummy_command, tmp_path):
    """Any other codesigning error raises an error."""
    # Raise an unknown error during codesign
    dummy_command.tools.subprocess.run.side_effect = mock_codesign("Unknown error")

    with pytest.raises(BriefcaseCommandError, match="Unable to code sign "):
        dummy_command.sign_file(
            tmp_path / "base_path" / "random.file",
            identity="Sekrit identity (DEADBEEF)",
        )

    # An attempt to codesign was made
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(
                tmp_path,
                tmp_path / "base_path" / "random.file",
                entitlements=False,
            ),
        ],
        any_order=False,
    )


def test_sign_app(dummy_command, first_app_with_binaries, tmp_path):
    """An app bundle can be signed."""
    # Sign the app
    dummy_command.sign_app(
        first_app_with_binaries, identity="Sekrit identity (DEADBEEF)"
    )

    # A request has been made to sign all the so and dylib files
    # This acts as a test of the discovery process:
    # * It discovers frameworks
    # * It discovers apps
    # * It discovers Mach-O binaries in various forms and guises
    # * It *doesn't* discover directories
    # * It *doesn't* discover non-Mach-O binaries
    # * It traverses in "depth first" order
    app_path = tmp_path / "base_path" / "macOS" / "app" / "First App" / "First App.app"
    lib_path = app_path / "Contents" / "Resources"
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(tmp_path, lib_path / "subfolder" / "second_so.so"),
            sign_call(tmp_path, lib_path / "subfolder" / "second_dylib.dylib"),
            sign_call(tmp_path, lib_path / "special.binary"),
            sign_call(tmp_path, lib_path / "other_binary"),
            sign_call(tmp_path, lib_path / "first_so.so"),
            sign_call(tmp_path, lib_path / "first_dylib.dylib"),
            sign_call(
                tmp_path, lib_path / "Extras.framework" / "Resources" / "extras.dylib"
            ),
            sign_call(tmp_path, lib_path / "Extras.framework"),
            sign_call(
                tmp_path, lib_path / "Extras.app" / "Contents" / "MacOS" / "Extras"
            ),
            sign_call(tmp_path, lib_path / "Extras.app"),
            sign_call(tmp_path, app_path),
        ],
        any_order=False,
    )
