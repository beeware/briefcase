import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_run(flatpak):
    """A Flatpak project can be executed."""

    flatpak.run(
        bundle="com.example",
        app_name="my-app",
    )

    # The expected call was made
    flatpak.subprocess.run.assert_called_once_with(
        [
            "flatpak",
            "run",
            "com.example.my-app",
        ],
        check=True,
    )


def test_run_fail(flatpak):
    """If execution fails, an error is raised."""
    flatpak.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd="flatpak install", returncode=1
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to start app my-app.",
    ):
        flatpak.run(
            bundle="com.example",
            app_name="my-app",
        )
