import subprocess

import pytest

from briefcase.console import LogLevel
from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize("tool_debug_mode", (True, False))
def test_bundle(flatpak, tool_debug_mode, tmp_path):
    """A Flatpak project can be bundled."""
    # Enable verbose tool logging
    if tool_debug_mode:
        flatpak.tools.logger.verbosity = LogLevel.DEEP_DEBUG

    flatpak.bundle(
        repo_url="https://example.com/flatpak",
        bundle_identifier="com.example.my-app",
        app_name="my-app",
        version="1.2.3",
        build_path=tmp_path / "build",
        output_path=tmp_path / "output/MyApp.flatpak",
    )

    # The expected call was made
    flatpak.tools.subprocess.run.assert_called_once_with(
        [
            "flatpak",
            "build-bundle",
            "--runtime-repo",
            "https://example.com/flatpak",
            "repo",
            tmp_path / "output/MyApp.flatpak",
            "com.example.my-app",
            "1.2.3",
        ]
        + (["--verbose"] if tool_debug_mode else []),
        check=True,
        cwd=tmp_path / "build",
    )


def test_bundle_fail(flatpak, tmp_path):
    """If bundling fails, an error is raised."""
    flatpak.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd="flatpak build-bundle", returncode=1
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to build a Flatpak bundle for app my-app.",
    ):
        flatpak.bundle(
            repo_url="https://example.com/flatpak",
            bundle_identifier="com.example.my-app",
            app_name="my-app",
            version="1.2.3",
            build_path=tmp_path / "build",
            output_path=tmp_path / "output/MyApp.flatpak",
        )
