import os
import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_verify_license_passes_quickly_if_license_present(mock_sdk):
    """Validate that verify_license() successfully does nothing in its happy
    path.

    If `android-sdk-license` exists in the right place, we expect
    verify_license() to run no subprocesses.
    """
    license_path = mock_sdk.root_path / "licenses" / "android-sdk-license"
    license_path.parent.mkdir(parents=True)
    license_path.touch()

    mock_sdk.verify_license()
    mock_sdk.command.subprocess.run.assert_not_called()


def test_verify_license_prompts_for_licenses_and_exits_if_you_agree(mock_sdk):
    """Validate that if verify_license() succeeds if you agree to the Android
    SDK license."""

    def accept_license(*args, **kwargs):
        license_dir = mock_sdk.root_path / "licenses"
        license_dir.mkdir(parents=True)
        (license_dir / "android-sdk-license").touch()

    mock_sdk.command.subprocess.run.side_effect = accept_license
    mock_sdk.verify_license()
    mock_sdk.command.subprocess.run.assert_called_once_with(
        [os.fsdecode(mock_sdk.sdkmanager_path), "--licenses"],
        env=mock_sdk.env,
        check=True,
    )


def test_verify_license_handles_sdkmanager_crash(mock_sdk):
    """Validate that if verify_license() raises a briefcase exception if it
    fails to launch `sdkmanager`."""
    mock_sdk.command.subprocess.run.side_effect = subprocess.CalledProcessError(1, "")
    with pytest.raises(BriefcaseCommandError):
        mock_sdk.verify_license()

    mock_sdk.command.subprocess.run.assert_called_once_with(
        [os.fsdecode(mock_sdk.sdkmanager_path), "--licenses"],
        env=mock_sdk.env,
        check=True,
    )


def test_verify_license_insists_on_agreement(mock_sdk):
    """Validate that if the user quits `sdkmanager --licenses` without agreeing
    to the license, verify_license() raises an exception."""
    # Simulate user non-acceptance of the license by allowing the mock
    # subprocess.run() to take no action.
    with pytest.raises(BriefcaseCommandError):
        mock_sdk.verify_license()

    mock_sdk.command.subprocess.run.assert_called_once_with(
        [os.fsdecode(mock_sdk.sdkmanager_path), "--licenses"],
        env=mock_sdk.env,
        check=True,
    )
