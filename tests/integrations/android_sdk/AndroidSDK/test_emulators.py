import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize(
    "output, expected_list",
    [
        ("", []),
        ("first\n", ["first"]),
        ("first\nsecond\nthird\n", ["first", "second", "third"]),
        ("first\n\nsecond", ["first", "second"]),
        (
            "first\nINFO    | Storing crashdata in\nsecond\nWARNING | nothing to see\n"
            "third\nERROR   | lot to see here",
            ["first", "second", "third"],
        ),
    ],
)
def test_no_emulators(mock_tools, android_sdk, output, expected_list):
    """The returned list of emulators is properly parsed."""
    mock_tools.subprocess.check_output.return_value = output

    assert android_sdk.emulators() == expected_list


def test_emulator_error(mock_tools, android_sdk):
    """If there is a problem invoking emulator, an error is returned."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=69, cmd="emulator -list-avd"
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to obtain Android emulator list",
    ):
        android_sdk.emulators()
