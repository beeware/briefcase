import subprocess

import pytest

from briefcase.console import LogLevel
from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize("tool_debug_mode", (True, False))
def test_verify_runtime(flatpak, tool_debug_mode):
    """A Flatpak runtime and SDK can be verified."""
    # Enable verbose tool logging
    if tool_debug_mode:
        flatpak.tools.logger.verbosity = LogLevel.DEEP_DEBUG

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
        ]
        + (["--verbose"] if tool_debug_mode else []),
        check=True,
        stream_output=False,
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
