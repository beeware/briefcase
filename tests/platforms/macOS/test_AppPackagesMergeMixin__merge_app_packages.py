import os
import subprocess
from pathlib import Path

import pytest

from briefcase.exceptions import BriefcaseCommandError

from ...utils import create_file, create_installed_package, file_content


@pytest.mark.parametrize("pre_existing", [True, False])
def test_merge(dummy_command, pre_existing, tmp_path):
    "Multiple source folders can be merged"
    if pre_existing:
        # Create some pre-existing package content. This should all be deleted as a
        # result of the merge process.
        create_installed_package(tmp_path / "merged_app_packages", "legacy")

    # Create 2 packages in the "gothic" architecture app package sources
    create_installed_package(tmp_path / "app_packages.gothic", "first", "1.2.3")
    create_installed_package(
        tmp_path / "app_packages.gothic",
        "second",
        "2.3.4",
        tag="macOS_11_0_gothic",
        extra_content=[
            ("second/other.py", "# other python"),
            ("second/different.py", "# different python"),
            ("second/some-binary", "# A file with executable permissions", 0o755),
            ("second/sub1/module1.dylib", "dylib-gothic"),
            ("second/sub1/module2.so", "dylib-gothic"),
            ("second/sub1/module3.dylib", "dylib-gothic"),
        ],
    )

    # Create 2 packages in the "modern" architecture app package sources
    # The first package is pure, so it won't exist in the second app_packages.
    # The "second" package:
    # - is missing the "other" python file and "module3" dylib
    # - has a "module4" dylib and an "extra" python file in a unique folder.
    create_installed_package(
        tmp_path / "app_packages.modern",
        "second",
        "2.3.4",
        tag="macOS_11_0_modern",
        extra_content=[
            ("second/different.py", "# I need to be different"),
            ("second/sub1/module1.dylib", "dylib-modern"),
            ("second/sub1/module2.so", "dylib-modern"),
            ("second/sub1/module4.dylib", "dylib-modern"),
            ("second/sub2/extra.py", "# extra python"),
        ],
    )

    # Mock subprocess so that lipo generates output files.
    def lipo(cmd, **kwargs):
        if cmd[0] != "lipo":
            pytest.fail(f"Subprocess called {cmd[0]}, not lipo")

        create_file(cmd[3], "dylib-merged")

    dummy_command.tools.subprocess.run.side_effect = lipo

    # Merge the two sources into a final location.
    merged_path = tmp_path / "merged_app_packages"
    dummy_command.merge_app_packages(
        merged_path,
        sources=[
            tmp_path / "app_packages.gothic",
            tmp_path / "app_packages.modern",
        ],
    )

    # The final merged app packages contains only the merged content.

    assert {
        (path.relative_to(merged_path), file_content(path))
        for path in merged_path.glob("**/*")
    } == {
        (Path("first"), None),
        (Path("first/__init__.py"), ""),
        (Path("first/app.py"), "# This is the app"),
        (Path("first-1.2.3.dist-info"), None),
        (Path("first-1.2.3.dist-info/INSTALLER"), "pip\n"),
        (
            Path("first-1.2.3.dist-info/METADATA"),
            "\n".join(
                [
                    "Metadata-Version: 2.1",
                    "Name: first",
                    "Version: 1.2.3",
                    "Summary: A packaged named first.",
                    "Author-email: Jane Developer <jane@example.com>",
                    "\n",
                ]
            ),
        ),
        (Path("first-1.2.3.dist-info/RECORD"), ""),
        (
            Path("first-1.2.3.dist-info/WHEEL"),
            "\n".join(
                [
                    "Wheel-Version: 1.0",
                    "Generator: test-case",
                    "Root-Is-Purelib: true",
                    "Tag: py3-none-any",
                    "\n",
                ]
            ),
        ),
        (Path("second"), None),
        (Path("second/__init__.py"), ""),
        (Path("second/app.py"), "# This is the app"),
        (Path("second/different.py"), "# different python"),
        (Path("second/some-binary"), "# A file with executable permissions"),
        (Path("second/other.py"), "# other python"),
        (Path("second/sub1"), None),
        (Path("second/sub1/module1.dylib"), "dylib-merged"),
        (Path("second/sub1/module2.so"), "dylib-merged"),
        (Path("second/sub1/module3.dylib"), "dylib-merged"),
        (Path("second/sub1/module4.dylib"), "dylib-merged"),
        (Path("second/sub2"), None),
        (Path("second/sub2/extra.py"), "# extra python"),
        (Path("second-2.3.4.dist-info"), None),
        (Path("second-2.3.4.dist-info/INSTALLER"), "pip\n"),
        (
            Path("second-2.3.4.dist-info/METADATA"),
            "\n".join(
                [
                    "Metadata-Version: 2.1",
                    "Name: second",
                    "Version: 2.3.4",
                    "Summary: A packaged named second.",
                    "Author-email: Jane Developer <jane@example.com>",
                    "\n",
                ]
            ),
        ),
        (Path("second-2.3.4.dist-info/RECORD"), ""),
        (
            Path("second-2.3.4.dist-info/WHEEL"),
            "\n".join(
                [
                    "Wheel-Version: 1.0",
                    "Generator: test-case",
                    "Root-Is-Purelib: false",
                    # The first source wins
                    "Tag: macOS_11_0_gothic",
                    "\n",
                ]
            ),
        ),
    }

    # Check that the embedded binary has executable permissions
    assert os.access(merged_path / "second/some-binary", os.X_OK)


def test_merge_problem(dummy_command, tmp_path):
    "If a binary cannot be merged, an exception is raised."

    # Create 2 packages in the "gothic" architecture app package sources
    create_installed_package(tmp_path / "app_packages.gothic", "first", "1.2.3")
    create_installed_package(
        tmp_path / "app_packages.gothic",
        "second",
        "2.3.4",
        tag="macOS_11_0_gothic",
        extra_content=[
            ("second/sub1/module1.dylib", "dylib-gothic"),
        ],
    )
    # Create 2 packages in the "modern" architecture app package sources
    # The first package is pure, so it won't exist in the second app_packages.
    # The "second" package:
    # - is missing the "other" python file and "module3" dylib
    # - has a "module4" dylib and an "extra" python file in a unique folder.
    create_installed_package(
        tmp_path / "app_packages.modern",
        "second",
        "2.3.4",
        tag="macOS_11_0_modern",
        extra_content=[
            ("second/sub1/module1.dylib", "dylib-modern"),
        ],
    )

    # Mock subprocess so that lipo generates an exception
    dummy_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="lipo"
    )

    # Merge the two sources into a final location. This will raise an exception.
    with pytest.raises(BriefcaseCommandError, match=r""):
        merged_path = tmp_path / "merged_app_packages"
        dummy_command.merge_app_packages(
            merged_path,
            sources=[
                tmp_path / "app_packages.gothic",
                tmp_path / "app_packages.modern",
            ],
        )


def test_merge_no_dylib(dummy_command, tmp_path, capsys):
    "If there are no dylibs, no merging is performed"

    # Create 2 pure python packages in the first app_packages folder.
    create_installed_package(tmp_path / "app_packages.gothic", "first", "1.2.3")
    create_installed_package(tmp_path / "app_packages.gothic", "second", "2.3.4")
    # Create an empty second app_packages folder.
    (tmp_path / "app_packages.modern").mkdir()

    # Merge the two sources into a final location.
    merged_path = tmp_path / "merged_app_packages"
    dummy_command.merge_app_packages(
        merged_path,
        sources=[
            tmp_path / "app_packages.gothic",
            tmp_path / "app_packages.modern",
        ],
    )

    # subprocess wasn't called.
    dummy_command.tools.subprocess.run.assert_not_called()

    # The final merged app packages contains only the merged content.
    assert {
        (path.relative_to(merged_path), file_content(path))
        for path in merged_path.glob("**/*")
    } == {
        (Path("first"), None),
        (Path("first/__init__.py"), ""),
        (Path("first/app.py"), "# This is the app"),
        (Path("first-1.2.3.dist-info"), None),
        (Path("first-1.2.3.dist-info/INSTALLER"), "pip\n"),
        (
            Path("first-1.2.3.dist-info/METADATA"),
            "\n".join(
                [
                    "Metadata-Version: 2.1",
                    "Name: first",
                    "Version: 1.2.3",
                    "Summary: A packaged named first.",
                    "Author-email: Jane Developer <jane@example.com>",
                    "\n",
                ]
            ),
        ),
        (Path("first-1.2.3.dist-info/RECORD"), ""),
        (
            Path("first-1.2.3.dist-info/WHEEL"),
            "\n".join(
                [
                    "Wheel-Version: 1.0",
                    "Generator: test-case",
                    "Root-Is-Purelib: true",
                    "Tag: py3-none-any",
                    "\n",
                ]
            ),
        ),
        (Path("second"), None),
        (Path("second/__init__.py"), ""),
        (Path("second/app.py"), "# This is the app"),
        (Path("second-2.3.4.dist-info"), None),
        (Path("second-2.3.4.dist-info/INSTALLER"), "pip\n"),
        (
            Path("second-2.3.4.dist-info/METADATA"),
            "\n".join(
                [
                    "Metadata-Version: 2.1",
                    "Name: second",
                    "Version: 2.3.4",
                    "Summary: A packaged named second.",
                    "Author-email: Jane Developer <jane@example.com>",
                    "\n",
                ]
            ),
        ),
        (Path("second-2.3.4.dist-info/RECORD"), ""),
        (
            Path("second-2.3.4.dist-info/WHEEL"),
            "\n".join(
                [
                    "Wheel-Version: 1.0",
                    "Generator: test-case",
                    "Root-Is-Purelib: true",
                    "Tag: py3-none-any",
                    "\n",
                ]
            ),
        ),
    }
