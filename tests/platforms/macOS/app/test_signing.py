import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from briefcase.commands.base import BaseCommand
from briefcase.console import Console, LogLevel
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS import SigningIdentity, macOSSigningMixin
from briefcase.platforms.macOS.app import macOSAppMixin
from tests.utils import DummyConsole


class DummySigningCommand(macOSAppMixin, macOSSigningMixin, BaseCommand):
    """A dummy command to expose code signing capabilities."""

    command = "sign"

    def __init__(self, base_path, **kwargs):
        kwargs.setdefault("console", Console())
        super().__init__(base_path=base_path / "base_path", **kwargs)
        self.tools.console = DummyConsole()


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
    identity,
    entitlements=True,
    runtime=True,
):
    """A test utility method to quickly construct a subprocess call to invoke codesign
    on a file."""
    args = [
        "codesign",
        filepath,
        "--sign",
        identity.id,
        "--force",
    ]
    if entitlements:
        args.extend(
            [
                "--entitlements",
                tmp_path / "base_path/build/first-app/macos/app/Entitlements.plist",
            ]
        )
    if runtime:
        args.extend(
            [
                "--options",
                "runtime",
            ]
        )

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


def test_explicit_app_identity_checksum(dummy_command):
    """If the user nominates an app identity by checksum, it is used."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
        "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # The identity will be the one the user specified as an option.
    result = dummy_command.select_identity("11E77FB58F13F6108B38110D5D92233C58ED38C5")

    assert result == SigningIdentity(
        id="11E77FB58F13F6108B38110D5D92233C58ED38C5",
        name="iPhone Developer: Jane Smith (BXAH5H869S)",
    )

    # User input was not solicited
    assert dummy_command.console.prompts == []


def test_explicit_app_identity_name(dummy_command):
    """If the user nominates an app identity by name, it is used."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
        "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # The identity will be the one the user specified as an option.
    result = dummy_command.select_identity("iPhone Developer: Jane Smith (BXAH5H869S)")

    assert result == SigningIdentity(
        id="11E77FB58F13F6108B38110D5D92233C58ED38C5",
        name="iPhone Developer: Jane Smith (BXAH5H869S)",
    )

    # User input was not solicited
    assert dummy_command.console.prompts == []


def test_invalid_app_identity_name(dummy_command):
    """If the user nominates an app identity by name, it is used."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
        "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # The identity will be the one the user specified as an option.
    with pytest.raises(BriefcaseCommandError):
        dummy_command.select_identity("not-an-identity")

    # User input was not solicited
    assert dummy_command.console.prompts == []


def test_implied_app_identity(dummy_command):
    """If there is only one app identity, it will still prompt with ad-hoc as a second
    option."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # Return option 2
    dummy_command.console.values = ["2"]

    result = dummy_command.select_identity()

    assert result == SigningIdentity(
        id="11E77FB58F13F6108B38110D5D92233C58ED38C5",
        name="iPhone Developer: Jane Smith (BXAH5H869S)",
    )

    # User input was solicited
    assert dummy_command.console.prompts == ["Application Signing Identity: "]


def test_no_app_identities(dummy_command):
    """If there are no identities the user will be prompted to select with only ad-hoc
    as an option."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {}

    # Return option 1
    dummy_command.console.values = ["1"]

    result = dummy_command.select_identity()

    # Result is the adhoc identity
    assert result == SigningIdentity()

    # User input was solicited
    assert dummy_command.console.prompts


def test_select_app_identity(dummy_command):
    """The user can select from a list of app identities."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
        "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # Return option 3
    dummy_command.console.values = ["3"]

    result = dummy_command.select_identity()

    # The identity will be second of the returned values
    assert result == SigningIdentity(
        id="11E77FB58F13F6108B38110D5D92233C58ED38C5",
        name="iPhone Developer: Jane Smith (BXAH5H869S)",
    )

    # User input was solicited once
    assert dummy_command.console.prompts == ["Application Signing Identity: "]


def test_select_app_identity_no_adhoc(dummy_command):
    """Adhoc identities can be excluded from the list of options."""
    # get_identities will return some options.
    dummy_command.get_identities.return_value = {
        "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
        "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
    }

    # Return option 2
    dummy_command.console.values = ["2"]

    # Disallow adhoc identities. This will make the identities from get_identities the
    # only available values.
    result = dummy_command.select_identity(allow_adhoc=False)

    # The identity will be second of the returned values
    assert result == SigningIdentity(
        id="11E77FB58F13F6108B38110D5D92233C58ED38C5",
        name="iPhone Developer: Jane Smith (BXAH5H869S)",
    )

    # User input was solicited once
    assert dummy_command.console.prompts == ["Application Signing Identity: "]


def test_select_installer_identity(dummy_command):
    """The user can select from a list of installer identities."""
    # get_identities is invoked twice - once with app identities, and once with all identities.
    dummy_command.get_identities.side_effect = [
        {
            "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
            "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
        },
        {
            "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
            "4C1067833814CE4738EBD6F8903EC63C238B0CA3": "Developer ID Installer: Example Corp Ltd (Z2K4383DLE)",
            "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
            "8903EC63C238B04C138EBD6F067833814CE47CA3": "Developer ID Installer: Example Corp Ltd (Z2K4383DLE)",
        },
    ]

    # Return option 2
    dummy_command.console.values = ["2"]

    result = dummy_command.select_identity(
        app_identity=SigningIdentity(
            id="38EBD6F8903EC63C238B04C1067833814CE47CA3",
            name="Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
        )
    )

    # The identity will be the second of the returned options; ad-hoc won't be added
    assert result == SigningIdentity(
        id="8903EC63C238B04C138EBD6F067833814CE47CA3",
        name="Developer ID Installer: Example Corp Ltd (Z2K4383DLE)",
    )

    # User input was solicited once
    assert dummy_command.console.prompts == ["Installer Signing Identity: "]


def test_installer_identity_matching_app(dummy_command):
    """The list of possible installer identities includes non-app identities from the
    same team."""
    # get_identities is invoked twice - once with app identities, and once with all identities.
    dummy_command.get_identities.side_effect = [
        {
            "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
            "EBD6F8903EC63C238B0384C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (83DLEZ2K43)",
            "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
        },
        {
            # The app identity that will be selected
            "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
            # A different app identity
            "EBD6F8903EC63C238B0384C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (83DLEZ2K43)",
            # An installer identity that doesn't match the selected app identity
            "1067833814CE4738EB4CD6F8903EC63C238B0CA3": "Developer ID Installer: Example Corp Ltd (83DLEZ2K43)",
            # An installer identity that *does* match the selected app identity
            "4C1067833814CE4738EBD6F8903EC63C238B0CA3": "Developer ID Installer: Example Corp Ltd (Z2K4383DLE)",
            # A different app identity
            "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
            # Another installer identity that match the selected app identity
            "8903EC63C238B04C138EBD6F067833814CE47CA3": "Developer ID Installer: Example Corp Ltd (Z2K4383DLE)",
        },
    ]

    # Return option 2
    dummy_command.console.values = ["2"]

    result = dummy_command.select_identity(
        app_identity=SigningIdentity(
            id="38EBD6F8903EC63C238B04C1067833814CE47CA3",
            name="Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
        )
    )

    # The identity will be the second of the returned options; ad-hoc won't be added,
    # and the installer identity for the other app identity won't be included
    assert result == SigningIdentity(
        id="8903EC63C238B04C138EBD6F067833814CE47CA3",
        name="Developer ID Installer: Example Corp Ltd (Z2K4383DLE)",
    )

    # User input was solicited once
    assert dummy_command.console.prompts == ["Installer Signing Identity: "]


def test_installer_identity_no_match(dummy_command):
    """The list of possible installer identities includes non-app identities from the
    same team."""
    # get_identities is invoked twice - once with app identities, and once with all identities.
    dummy_command.get_identities.side_effect = [
        {
            "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
            "EBD6F8903EC63C238B0384C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (83DLEZ2K43)",
            "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
        },
        {
            # The app identity that will be selected
            "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
            # A different app identity
            "EBD6F8903EC63C238B0384C1067833814CE47CA3": "Developer ID Application: Example Corp Ltd (83DLEZ2K43)",
            # An installer identity that doesn't match the selected app identity
            "1067833814CE4738EB4CD6F8903EC63C238B0CA3": "Developer ID Installer: Example Corp Ltd (83DLEZ2K43)",
            # A different app identity
            "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
        },
    ]

    # As there are no viable installer certificates, an error is raised.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"No installer signing identities for team Z2K4383DLE could be found.",
    ):
        dummy_command.select_identity(
            app_identity=SigningIdentity(
                id="38EBD6F8903EC63C238B04C1067833814CE47CA3",
                name="Developer ID Application: Example Corp Ltd (Z2K4383DLE)",
            )
        )

    # User input was never solicited once
    assert dummy_command.console.prompts == []


@pytest.mark.parametrize("verbose", [True, False])
def test_sign_file_adhoc_identity(
    dummy_command,
    adhoc_identity,
    verbose,
    tmp_path,
    capsys,
):
    """If an ad-hoc identity is used, the runtime option isn't used."""
    if verbose:
        dummy_command.console.verbosity = LogLevel.VERBOSE

    # Sign the file with an ad-hoc identity
    dummy_command.sign_file(tmp_path / "base_path/random.file", identity=adhoc_identity)

    # An attempt to codesign was made without the runtime option
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(
                tmp_path,
                tmp_path / "base_path/random.file",
                identity=adhoc_identity,
                entitlements=False,
                runtime=False,
            ),
        ],
        any_order=False,
    )

    # No console output
    output = capsys.readouterr().out
    assert len(output.strip("\n").split("\n")) == 1


@pytest.mark.parametrize("verbose", [True, False])
def test_sign_file_entitlements(
    dummy_command,
    sekrit_identity,
    verbose,
    tmp_path,
    capsys,
):
    """Entitlements can be included in a signing call."""
    if verbose:
        dummy_command.console.verbosity = LogLevel.VERBOSE

    # Sign the file with an ad-hoc identity
    dummy_command.sign_file(
        tmp_path / "base_path/random.file",
        identity=sekrit_identity,
        entitlements=tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "Entitlements.plist",
    )

    # An attempt to codesign was made without the runtime option
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(
                tmp_path,
                tmp_path / "base_path/random.file",
                identity=sekrit_identity,
            ),
        ],
        any_order=False,
    )

    # No console output
    output = capsys.readouterr().out
    assert len(output.strip("\n").split("\n")) == 1


@pytest.mark.parametrize("verbose", [True, False])
def test_sign_file_unsupported_format(
    dummy_command,
    sekrit_identity,
    verbose,
    tmp_path,
    capsys,
):
    """If codesign reports an unsupported format, the signing attempt is ignored with a
    warning."""
    if verbose:
        dummy_command.console.verbosity = LogLevel.VERBOSE

    # FIXME: I'm not sure how to manufacture this in practice.
    dummy_command.tools.subprocess.run.side_effect = mock_codesign(
        "unsupported format for signature"
    )

    # Sign the file
    dummy_command.sign_file(
        tmp_path / "base_path/random.file",
        identity=sekrit_identity,
    )

    # An attempt to codesign was made
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(
                tmp_path,
                tmp_path / "base_path/random.file",
                identity=sekrit_identity,
                entitlements=False,
            ),
        ],
        any_order=False,
    )

    output = capsys.readouterr().out
    if verbose:
        # The console includes a warning about not needing a signature.
        assert "... random.file does not require a signature\n" in output

    # Output only happens if in debug mode
    assert len(output.strip("\n").split("\n")) == (2 if verbose else 1)


@pytest.mark.parametrize("verbose", [True, False])
def test_sign_file_unknown_bundle_format(
    dummy_command,
    sekrit_identity,
    verbose,
    tmp_path,
    capsys,
):
    """If a folder happens to have a .framework extension, the signing attempt is
    ignored with a warning."""
    if verbose:
        dummy_command.console.verbosity = LogLevel.VERBOSE

    # Raise an error caused by an unknown bundle format during codesign
    dummy_command.tools.subprocess.run.side_effect = mock_codesign(
        "bundle format unrecognized, invalid, or unsuitable"
    )

    # Sign the file
    dummy_command.sign_file(
        tmp_path / "base_path/random.file",
        identity=sekrit_identity,
    )

    # An attempt to codesign was made
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(
                tmp_path,
                tmp_path / "base_path/random.file",
                identity=sekrit_identity,
                entitlements=False,
            ),
        ],
        any_order=False,
    )

    output = capsys.readouterr().out
    if verbose:
        # The console includes a warning about not needing a signature.
        assert "... random.file does not require a signature\n" in output

    # Output only happens if in debug mode
    assert len(output.strip("\n").split("\n")) == (2 if verbose else 1)


@pytest.mark.parametrize("verbose", [True, False])
def test_sign_file_unknown_error(
    dummy_command,
    sekrit_identity,
    verbose,
    tmp_path,
    capsys,
):
    """Any other codesigning error raises an error."""
    if verbose:
        dummy_command.console.verbosity = LogLevel.VERBOSE

    # Raise an unknown error during codesign
    dummy_command.tools.subprocess.run.side_effect = mock_codesign("Unknown error")

    with pytest.raises(BriefcaseCommandError, match="Unable to code sign "):
        dummy_command.sign_file(
            tmp_path / "base_path/random.file",
            identity=sekrit_identity,
        )

    # An attempt to codesign was made
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(
                tmp_path,
                tmp_path / "base_path/random.file",
                identity=sekrit_identity,
                entitlements=False,
            ),
        ],
        any_order=False,
    )

    # No console output
    output = capsys.readouterr().out
    assert len(output.strip("\n").split("\n")) == 1


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Can't test macOS codesigning on Windows",
)
@pytest.mark.parametrize("verbose", [True, False])
def test_sign_app(
    dummy_command,
    sekrit_identity,
    first_app_with_binaries,
    verbose,
    tmp_path,
    capsys,
):
    """An app bundle can be signed."""
    if verbose:
        dummy_command.console.verbosity = LogLevel.VERBOSE

    # Sign the app
    dummy_command.sign_app(
        first_app_with_binaries,
        identity=sekrit_identity,
    )

    # A request has been made to sign all the so and dylib files
    # This acts as a test of the discovery process:
    # * It discovers frameworks
    # * It discovers apps
    # * It discovers Mach-O binaries in various forms and guises
    # * It *doesn't* discover directories
    # * It *doesn't* discover non-Mach-O binaries
    # * It traverses in "depth first" order
    app_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "First App.app"
    )
    lib_path = app_path / "Contents/Resources/app_packages"
    frameworks_path = app_path / "Contents/Frameworks"

    assert len(dummy_command.tools.subprocess.run.mock_calls) == 11
    dummy_command.tools.subprocess.run.assert_has_calls(
        [
            sign_call(
                tmp_path,
                lib_path / "subfolder/second_so.so",
                identity=sekrit_identity,
            ),
            sign_call(
                tmp_path,
                lib_path / "subfolder/second_dylib.dylib",
                identity=sekrit_identity,
            ),
            sign_call(
                tmp_path,
                lib_path / "special.binary",
                identity=sekrit_identity,
            ),
            sign_call(
                tmp_path,
                lib_path / "other_binary",
                identity=sekrit_identity,
            ),
            sign_call(
                tmp_path,
                lib_path / "first_so.so",
                identity=sekrit_identity,
            ),
            sign_call(
                tmp_path,
                lib_path / "first_dylib.dylib",
                identity=sekrit_identity,
            ),
            sign_call(
                tmp_path,
                lib_path / "Extras.app/Contents/MacOS/Extras",
                identity=sekrit_identity,
            ),
            sign_call(
                tmp_path,
                lib_path / "Extras.app",
                identity=sekrit_identity,
            ),
            sign_call(
                tmp_path,
                frameworks_path / "Extras.framework/Versions/1.2/libs/extras.dylib",
                identity=sekrit_identity,
            ),
            sign_call(
                tmp_path,
                frameworks_path / "Extras.framework",
                identity=sekrit_identity,
            ),
            sign_call(
                tmp_path,
                app_path,
                identity=sekrit_identity,
            ),
        ],
        any_order=True,
    )

    # Also check that files are not signed after their parent directory has been
    # signed. Reduce the files mentions in the calls to the dummy command
    # to a list of path objects, then ensure that the call to sign any given file
    # does not occur *after* it's parent directory.
    sign_targets = [
        Path(call.args[0][1]) for call in dummy_command.tools.subprocess.run.mock_calls
    ]

    parents = set()
    for path in sign_targets:
        # Check parent of path is not in parents
        assert path.parent not in parents
        parents.add(path)

    # Output only happens if in debug mode.
    output = capsys.readouterr().out
    assert len(output.strip("\n").split("\n")) == (11 if verbose else 1)


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Can't test macOS codesigning on Windows",
)
@pytest.mark.parametrize("verbose", [True, False])
def test_sign_app_with_failure(
    dummy_command,
    sekrit_identity,
    first_app_with_binaries,
    verbose,
    capsys,
):
    """If signing a single file in the app fails, the error is surfaced."""
    if verbose:
        dummy_command.console.verbosity = LogLevel.VERBOSE

    # Sign the app. Signing first_dylib.dylib will fail.
    def _codesign(args, **kwargs):
        if Path(args[1]).name == "first_dylib.dylib":
            raise subprocess.CalledProcessError(
                returncode=1, cmd=args, stderr=f"{args[1]}: Unknown error"
            )

    dummy_command.tools.subprocess.run.side_effect = _codesign

    # The invocation will raise an error; however, we can't predict exactly which
    # file will raise an error.
    with pytest.raises(
        BriefcaseCommandError, match=r"Unable to code sign .*first_dylib\.dylib"
    ):
        dummy_command.sign_app(
            first_app_with_binaries,
            identity=sekrit_identity,
        )

    # There has been at least 1 call to sign files. We can't know how many are
    # actually signed, as threads are involved.
    dummy_command.tools.subprocess.run.call_count > 0

    # Output only happens if in debug mode.
    output = capsys.readouterr().out
    assert len(output.strip("\n").split("\n")) == (8 if verbose else 1)
