import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_verify_runtime(flatpak):
    """A Flatpak runtime and SDK can be verified."""

    flatpak.verify_runtime(
        repo_alias="test-alias",
        runtime="org.beeware.flatpak.Platform",
        runtime_version="37.42",
        sdk="org.beeware.flatpak.SDK",
    )

    # The expected call was made
    flatpak.tools.subprocess.run.assert_called_once_with(
        [
            "flatpak",
            "install",
            "--assumeyes",
            "--user",
            "test-alias",
            "org.beeware.flatpak.Platform/gothic/37.42",
            "org.beeware.flatpak.SDK/gothic/37.42",
        ],
        check=True,
    )


def test_verify_runtime_fail(flatpak):
    """If runtime verification fails, an error is raised."""
    flatpak.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd="flatpak install", returncode=1
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Unable to install Flatpak runtime org.beeware.flatpak.Platform/gothic/37.42 "
            r"and SDK org.beeware.flatpak.SDK/gothic/37.42 from repo test-alias."
        ),
    ):
        flatpak.verify_runtime(
            repo_alias="test-alias",
            runtime="org.beeware.flatpak.Platform",
            runtime_version="37.42",
            sdk="org.beeware.flatpak.SDK",
        )
