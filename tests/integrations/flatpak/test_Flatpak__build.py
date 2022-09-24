import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_build(flatpak, tmp_path):
    """A Flatpak project can be built."""
    flatpak.build(
        bundle="com.example",
        app_name="my-app",
        path=tmp_path,
    )

    # The expected call was made
    flatpak.tools.subprocess.run.assert_called_once_with(
        [
            "flatpak-builder",
            "--force-clean",
            "--repo",
            "repo",
            "--install",
            "--user",
            "build",
            "manifest.yml",
        ],
        check=True,
        cwd=tmp_path,
    )

    # The marker file was created, and was made executable
    assert (tmp_path / "com.example.my-app").exists()
    flatpak.tools.os.chmod.assert_called_once_with(
        tmp_path / "com.example.my-app", 0o755
    )


def test_build_fail(flatpak, tmp_path):
    """If the build fails, an error is raised."""
    flatpak.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd="flatpak-builder", returncode=1
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Error while building app my-app.",
    ):
        flatpak.build(
            bundle="com.example",
            app_name="my-app",
            path=tmp_path / "bundle",
        )
