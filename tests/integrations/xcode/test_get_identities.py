import subprocess
from pathlib import Path

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import get_identities


def security_result(name):
    """Load a security result file from the sample directory, and return the content."""
    filename = Path(__file__).parent / "security" / f"{name}.out"
    with filename.open(encoding="utf-8") as f:
        return f.read()


def test_security_missing(mock_tools):
    """If security is missing or fails to start, an exception is raised."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["security", "find-identities", "-v", "-p", "codesigning"], returncode=1
    )

    with pytest.raises(BriefcaseCommandError):
        get_identities(mock_tools, "codesigning")


def test_invalid_profile(mock_tools):
    """If the requested profile is invalid, an exception is raised."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["security", "find-identities", "-v", "-p", "jabberwock"], returncode=2
    )

    with pytest.raises(BriefcaseCommandError):
        get_identities(mock_tools, "codesigning")


def test_no_identities(mock_tools):
    """If there are no identities available, no simulators will be found."""
    mock_tools.subprocess.check_output.return_value = security_result("no-identities")

    simulators = get_identities(mock_tools, "codesigning")

    assert simulators == {}


def test_one_identity(mock_tools):
    """If there is one identity available, it is returned."""
    mock_tools.subprocess.check_output.return_value = security_result("one-identity")

    simulators = get_identities(mock_tools, "codesigning")

    assert simulators == {
        "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corporation Ltd (Z2K4383DLE)",
    }


def test_multiple_identities(mock_tools):
    """If there are multiple identities available, they are all returned."""
    mock_tools.subprocess.check_output.return_value = security_result(
        "multiple-identities"
    )

    simulators = get_identities(mock_tools, "codesigning")

    assert simulators == {
        "38EBD6F8903EC63C238B04C1067833814CE47CA3": "Developer ID Application: Example Corporation Ltd (Z2K4383DLE)",
        "11E77FB58F13F6108B38110D5D92233C58ED38C5": "iPhone Developer: Jane Smith (BXAH5H869S)",
        "F8903EC63C238B04C1067833814CE47CA338EBD6": "Developer ID Application: Other Corporation Ltd (83DLZ2K43E)",
    }
