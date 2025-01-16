import platform
import subprocess
from zipfile import ZipFile

import pytest

from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.skipif(
    platform.system() != "Darwin",
    reason="ditto tests can only be performed on macOS",
)
def test_ditto(
    package_command,
    first_app_with_binaries,
    tmp_path,
):
    """An app archive can be built with ditto."""
    app_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "First App.app"
    )
    archive_path = tmp_path / "base_path/build/first-app/macos/app/archive.zip"

    # Reconnect the subprocess.run with its live implementation
    package_command.tools.subprocess.run.side_effect = subprocess.run

    # Build the ditto archive
    package_command.ditto_archive(app_path, archive_path)

    # The archive contains the app as the only top level element.
    with ZipFile(archive_path) as archive:
        assert sorted(archive.namelist()) == [
            "First App.app/",
            "First App.app/Contents/",
            "First App.app/Contents/Frameworks/",
            "First App.app/Contents/Frameworks/Extras.framework/",
            "First App.app/Contents/Frameworks/Extras.framework/Extras",
            "First App.app/Contents/Frameworks/Extras.framework/Resources/",
            "First App.app/Contents/Frameworks/Extras.framework/Resources/Info.plist",
            "First App.app/Contents/Frameworks/Extras.framework/Versions/",
            "First App.app/Contents/Frameworks/Extras.framework/Versions/1.2/",
            "First App.app/Contents/Frameworks/Extras.framework/Versions/1.2/Extras",
            "First App.app/Contents/Frameworks/Extras.framework/Versions/1.2/libs/",
            "First App.app/Contents/Frameworks/Extras.framework/Versions/1.2/libs/extras.dylib",
            "First App.app/Contents/Frameworks/Extras.framework/Versions/Current",
            "First App.app/Contents/Info.plist",
            "First App.app/Contents/MacOS/",
            "First App.app/Contents/MacOS/First App",
            "First App.app/Contents/Resources/",
            "First App.app/Contents/Resources/app_packages/",
            "First App.app/Contents/Resources/app_packages/Extras.app/",
            "First App.app/Contents/Resources/app_packages/Extras.app/Contents/",
            "First App.app/Contents/Resources/app_packages/Extras.app/Contents/MacOS/",
            "First App.app/Contents/Resources/app_packages/Extras.app/Contents/MacOS/Extras",
            "First App.app/Contents/Resources/app_packages/first.other",
            "First App.app/Contents/Resources/app_packages/first_dylib.dylib",
            "First App.app/Contents/Resources/app_packages/first_so.so",
            "First App.app/Contents/Resources/app_packages/other_binary",
            "First App.app/Contents/Resources/app_packages/second.other",
            "First App.app/Contents/Resources/app_packages/special.binary",
            "First App.app/Contents/Resources/app_packages/subfolder/",
            "First App.app/Contents/Resources/app_packages/subfolder/second_dylib.dylib",
            "First App.app/Contents/Resources/app_packages/subfolder/second_so.so",
            "First App.app/Contents/Resources/app_packages/unknown.binary",
        ]


@pytest.mark.skipif(
    platform.system() != "Darwin",
    reason="ditto tests can only be performed on macOS",
)
def test_ditto_failure(
    package_command,
    first_app_with_binaries,
    tmp_path,
):
    """If ditto fails, an error is raised."""
    app_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "First App.app"
    )
    archive_path = tmp_path / "base_path/build/first-app/macos/app/archive.zip"

    # Reconnect the subprocess.run with its live implementation
    package_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        1, cmd=["ditto"]
    )

    # Build the ditto archive
    with pytest.raises(BriefcaseCommandError, match=r"Unable to archive First App.app"):
        package_command.ditto_archive(app_path, archive_path)
