import subprocess

import pytest

from briefcase.console import LogLevel
from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize("tool_debug_mode", (True, False))
def test_verify_repo(flatpak, tool_debug_mode):
    """A Flatpak repo can be verified."""
    # Enable verbose tool logging
    if tool_debug_mode:
        flatpak.tools.logger.verbosity = LogLevel.DEEP_DEBUG

    flatpak.verify_repo(
        repo_alias="test-alias",
        url="https://example.com/flatpak",
    )

    # The expected call was made
    flatpak.tools.subprocess.run.assert_called_once_with(
        [
            "flatpak",
            "remote-add",
            "--user",
            "--if-not-exists",
            "test-alias",
            "https://example.com/flatpak",
        ]
        + (["--verbose"] if tool_debug_mode else []),
        check=True,
    )


def test_verify_repo_fail(flatpak):
    """If repo verification fails, an error is raised."""
    flatpak.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd="flatpak repo-add", returncode=1
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to add Flatpak repo https://example.com/flatpak with alias test-alias.",
    ):
        flatpak.verify_repo(
            repo_alias="test-alias",
            url="https://example.com/flatpak",
        )
