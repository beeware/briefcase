import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError

from ...utils import create_file, create_installed_package, file_content


def test_thin_app_packages(dummy_command, tmp_path):
    "An app packages folder can be thinned"
    app_packages = tmp_path / "app_pacakges.gothic"

    # Install a package into the app_packages folder that contains source and binaries.
    create_installed_package(
        app_packages,
        "pkg",
        "2.3.4",
        tag="macOS_11_0_gothic",
        extra_content=[
            ("pkg/other.py", "# other python"),
            ("pkg/sub1/module1.dylib", "dylib-fat"),
            ("pkg/sub1/module2.so", "dylib-fat"),
            ("pkg/sub2/module3.dylib", "dylib-fat"),
        ],
    )

    # All dylibs have 2 architectures
    dummy_command.tools.subprocess.check_output.return_value = (
        "Architectures in the fat file: path/to/file.dylib are: modern gothic\n"
    )

    # Mock the effect of calling lipo -thin
    def thin_dylib(*args, **kwargs):
        create_file(args[0][args[0].index("-output") + 1], "dylib-thin")

    dummy_command.tools.subprocess.run.side_effect = thin_dylib

    # Thin the app_packages folder to gothic dylibs
    dummy_command.thin_app_packages(app_packages, arch="gothic")

    # All libraries have been thinned
    assert file_content(app_packages / "pkg/sub1/module1.dylib") == "dylib-thin"
    assert file_content(app_packages / "pkg/sub1/module2.so") == "dylib-thin"
    assert file_content(app_packages / "pkg/sub2/module3.dylib") == "dylib-thin"


def test_thin_app_packages_problem(dummy_command, tmp_path):
    "If one of the libraries can't be thinned, an error is raised"
    app_packages = tmp_path / "app_pacakges.gothic"

    # Install a package into the app_packages folder that contains source and binaries.
    create_installed_package(
        app_packages,
        "pkg",
        "2.3.4",
        tag="macOS_11_0_gothic",
        extra_content=[
            ("pkg/other.py", "# other python"),
            ("pkg/sub1/module1.dylib", "dylib-fat"),
            ("pkg/sub1/module2.so", "dylib-fat"),
            ("pkg/sub2/module3.dylib", "dylib-fat"),
        ],
    )

    # All dylibs have 2 architectures
    dummy_command.tools.subprocess.check_output.return_value = (
        "Architectures in the fat file: path/to/file.dylib are: modern gothic\n"
    )

    # Mock the effect of calling lipo -thin. Calling on a .so file raises an error.
    def thin_dylib(*args, **kwargs):
        if str(args[0][-1]).endswith(".so"):
            raise subprocess.CalledProcessError(cmd="lipo -thin", returncode=-1)
        create_file(args[0][args[0].index("-output") + 1], "dylib-thin")

    dummy_command.tools.subprocess.run.side_effect = thin_dylib

    # Thin the app_packages folder to gothic dylibs. This raises an error:
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to create thin binary from .*module2\.so",
    ):
        dummy_command.thin_app_packages(app_packages, arch="gothic")


def test_thin_no_dylibs(dummy_command, tmp_path):
    "If there are no dylibs, thinning is a no-op."
    app_packages = tmp_path / "app_pacakges.gothic"

    # Install a package into the app_packages folder that only contains source.
    create_installed_package(
        app_packages,
        "pkg",
        "2.3.4",
        tag="macOS_11_0_gothic",
        extra_content=[
            ("pkg/other.py", "# other python"),
        ],
    )

    # Thin the app packages folder
    dummy_command.thin_app_packages(app_packages, arch="gothic")

    # lipo was not called.
    dummy_command.tools.subprocess.check_output.assert_not_called()
    dummy_command.tools.subprocess.run.assert_not_called()
