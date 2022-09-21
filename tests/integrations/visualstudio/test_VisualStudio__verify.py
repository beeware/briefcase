import json
import os
import subprocess
from pathlib import Path
from unittest.mock import call

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.visualstudio import VisualStudio

MSBUILD_OUTPUT = """Microsoft (R) Build Engine version 17.2.1+52cd2da31 for .NET Framework
Copyright (C) Microsoft Corporation. All rights reserved.

17.2.1.25201
"""


@pytest.fixture
def custom_msbuild_path(tmp_path):
    """Create a dummy MSBuild executable at a custom location."""
    msbuild_path = tmp_path / "custom" / "MSBuild.exe"
    msbuild_path.parent.mkdir(parents=True)
    with msbuild_path.open("w") as f:
        f.write("Dummy MSBuild")

    return msbuild_path


@pytest.fixture
def vswhere_path(tmp_path):
    """Create a dummy vswhere executable."""
    vswhere_path = (
        tmp_path
        / "Program Files (x86)"
        / "Microsoft Visual Studio"
        / "Installer"
        / "vswhere.exe"
    )

    vswhere_path.parent.mkdir(parents=True)
    with vswhere_path.open("w") as f:
        f.write("Dummy vswhere")

    return vswhere_path


@pytest.fixture
def msbuild_path(tmp_path):
    """Create a dummy MSBuild executable."""
    msbuild_path = (
        tmp_path / "Visual Studio" / "MSBuild" / "Current" / "Bin" / "MSBuild.exe"
    )
    msbuild_path.parent.mkdir(parents=True)
    with msbuild_path.open("w") as f:
        f.write("Dummy MSBuild")

    return msbuild_path


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.visualstudio = "tool"

    tool = VisualStudio.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.visualstudio


def test_msbuild_on_path(mock_tools):
    """If MSBuild is on the path, that version is used."""
    # MSBuild is on the path, so check_output succeeds
    mock_tools.subprocess.check_output.return_value = MSBUILD_OUTPUT

    # Verify the installation
    visualstudio = VisualStudio.verify(mock_tools)

    # Visual studio is configured to use an MSBuild with no path,
    # which provides no metadata.
    assert visualstudio.msbuild_path == Path("MSBuild.exe")
    assert visualstudio.install_metadata is None

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT)],
        any_order=False,
    )


def test_msbuild_on_path_corrupt(mock_tools):
    """If MSBuild is on the path, but it cannot be invoked, an error is
    raised."""
    # MSBuild is on the path, but raises an error when invoked
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd="MSBuild.exe",
    )

    # Verify the installation
    with pytest.raises(
        BriefcaseCommandError,
        match=r"MSBuild is on the path, but Briefcase cannot start it.",
    ):
        VisualStudio.verify(mock_tools)

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT)],
        any_order=False,
    )


def test_msbuild_envvar(mock_tools, custom_msbuild_path):
    """If MSBUILD is set in the environment, that executable is used."""
    # Point at the dummy MSBuild executable
    mock_tools.os.environ["MSBUILD"] = custom_msbuild_path

    # MSBuild is not on the path, but the
    mock_tools.subprocess.check_output.side_effect = [
        FileNotFoundError,  # Not on path
        0,  # Custom location succeeds
    ]

    # Verify the installation
    visualstudio = VisualStudio.verify(mock_tools)

    # Visual studio is configured to use an MSBuild at the specified path
    # which provides no metadata.
    assert visualstudio.msbuild_path == custom_msbuild_path
    assert visualstudio.install_metadata is None

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT),
            call([custom_msbuild_path, "--version"], stderr=subprocess.STDOUT),
        ],
        any_order=False,
    )


def test_msbuild_envvar_doesnt_exist(mock_tools, tmp_path):
    """If MSBUILD is set in the environment, but it points to a non-existent
    file, an error is raised."""
    # Point at an MSBuild that does not exist
    mock_tools.os.environ["MSBUILD"] = tmp_path / "custom" / "MSBuild.exe"

    # MSBuild is not on the path
    mock_tools.subprocess.check_output.side_effect = FileNotFoundError

    # Verify the installation
    with pytest.raises(
        BriefcaseCommandError,
        match=r"The location referenced by the environment variable MSBUILD:",
    ):
        VisualStudio.verify(mock_tools)

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT),
        ],
        any_order=False,
    )


def test_msbuild_envvar_bad_executable(mock_tools, custom_msbuild_path):
    """If MSBUILD is set in the environment, but it can't be invoked, an error
    is raised."""
    # Point at the dummy MSBuild executable
    mock_tools.os.environ["MSBUILD"] = custom_msbuild_path

    # MSBuild is not on the path, and can't be invoked at the custom location
    mock_tools.subprocess.check_output.side_effect = [
        FileNotFoundError,  # Not on path
        subprocess.CalledProcessError(-1, custom_msbuild_path),  # Custom location fails
    ]

    # Verify the installation
    with pytest.raises(
        BriefcaseCommandError,
        match=r"MSBuild appears to exist, but Briefcase can't start it.",
    ):
        VisualStudio.verify(mock_tools)

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT),
            call([custom_msbuild_path, "--version"], stderr=subprocess.STDOUT),
        ],
        any_order=False,
    )


def test_vswhere_does_not_exist(mock_tools):
    """If VSWhere does not exist, an error is raised."""
    # MSBuild is not on the path
    mock_tools.subprocess.check_output.side_effect = FileNotFoundError

    # Verify the installation
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Visual Studio does not appear to be installed.",
    ):
        VisualStudio.verify(mock_tools)

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT),
        ],
        any_order=False,
    )


def test_vswhere_bad_executable(mock_tools, vswhere_path):
    """If VSWhere exists, but cannot be executed, an error is raised."""
    # MSBuild is not on the path, and vswhere raises an error
    mock_tools.subprocess.check_output.side_effect = [
        FileNotFoundError,  # MSBuild not on path
        subprocess.CalledProcessError(returncode=1, cmd=vswhere_path),  # vswhere fails
    ]

    # Verify the installation
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Visual Studio appears to exist, but Briefcase can't retrieve installation metadata.",
    ):
        VisualStudio.verify(mock_tools)

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT),
            call(
                [vswhere_path, "-latest", "-prerelease", "-format", "json"],
                stderr=subprocess.STDOUT,
            ),
        ],
        any_order=False,
    )


def test_vswhere_bad_content(mock_tools, vswhere_path):
    """If VSWhere can be executed, but returns garbage content, an error is
    raised."""
    # MSBuild is not on the path, and vswhere returns non-JSON content
    mock_tools.subprocess.check_output.side_effect = [
        FileNotFoundError,  # MSBuild not on path
        "This is not JSON content",  # vswhere returns non-JSON content
    ]

    # Verify the installation
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Visual Studio appears to exist, but Briefcase can't retrieve installation metadata.",
    ):
        VisualStudio.verify(mock_tools)

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT),
            call(
                [vswhere_path, "-latest", "-prerelease", "-format", "json"],
                stderr=subprocess.STDOUT,
            ),
        ],
        any_order=False,
    )


def test_vswhere_non_list_content(mock_tools, vswhere_path):
    """If VSWhere can be executed, but the outermost content isn't a list, an
    error is raised."""
    # MSBuild is not on the path, and vswhere returns JSON content, but not in the format expected
    mock_tools.subprocess.check_output.side_effect = [
        FileNotFoundError,  # MSBuild not on path
        '{"problem": "JSON but not a list"}',  # vswhere returns JSON content, but not as a list.
    ]

    # Verify the installation
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Visual Studio appears to exist, but Briefcase can't retrieve installation metadata.",
    ):
        VisualStudio.verify(mock_tools)

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT),
            call(
                [vswhere_path, "-latest", "-prerelease", "-format", "json"],
                stderr=subprocess.STDOUT,
            ),
        ],
        any_order=False,
    )


def test_vswhere_empty_list_content(mock_tools, vswhere_path):
    """If VSWhere can be executed, but the outermost content is an empty list,
    an error is raised."""
    # MSBuild is not on the path, and vswhere returns JSON content, but not in the format expected
    mock_tools.subprocess.check_output.side_effect = [
        FileNotFoundError,  # MSBuild not on path
        "[]",  # vswhere returns empty list JSON content
    ]

    # Verify the installation
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Visual Studio appears to exist, but Briefcase can't retrieve installation metadata.",
    ):
        VisualStudio.verify(mock_tools)

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT),
            call(
                [vswhere_path, "-latest", "-prerelease", "-format", "json"],
                stderr=subprocess.STDOUT,
            ),
        ],
        any_order=False,
    )


def test_vswhere_msbuild_not_installed(mock_tools, tmp_path, vswhere_path):
    """If VSWhere can be executed, but it doesn't point at an MSBuild
    executable, an error is raised."""
    # MSBuild is not on the path; vswhere a valid location, but there's no MSBuild there.
    mock_tools.subprocess.check_output.side_effect = [
        FileNotFoundError,  # MSBuild not on path
        json.dumps(
            [
                {
                    "instanceId": "deadbeef",
                    "installDate": "2022-07-14T10:42:37Z",
                    "installationPath": os.fsdecode(tmp_path / "Visual Studio"),
                }
            ]
        ),  # vswhere returns JSON content
    ]

    # Verify the installation
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Your Visual Studio installation does not appear to provide MSBuild.",
    ):
        VisualStudio.verify(mock_tools)

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT),
            call(
                [vswhere_path, "-latest", "-prerelease", "-format", "json"],
                stderr=subprocess.STDOUT,
            ),
        ],
        any_order=False,
    )


def test_vswhere_msbuild_bad_executable(
    mock_tools,
    tmp_path,
    vswhere_path,
    msbuild_path,
):
    """If VSWhere points at an MSBuild executable, but that exe can't be
    started, an error is raised."""
    # MSBuild is not on the path; vswhere a valid location, but MSBuild fails.
    mock_tools.subprocess.check_output.side_effect = [
        FileNotFoundError,  # MSBuild not on path
        json.dumps(
            [
                {
                    "instanceId": "deadbeef",
                    "installDate": "2022-07-14T10:42:37Z",
                    "installationPath": os.fsdecode(tmp_path / "Visual Studio"),
                }
            ]
        ),  # vswhere returns JSON content
        subprocess.CalledProcessError(
            returncode=1,
            cmd="MSBuild.exe",
        ),  # MSBuild fails
    ]

    # Verify the installation
    with pytest.raises(
        BriefcaseCommandError,
        match=r"MSBuild appears to exist, but Briefcase can't start it.",
    ):
        VisualStudio.verify(mock_tools)

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT),
            call(
                [vswhere_path, "-latest", "-prerelease", "-format", "json"],
                stderr=subprocess.STDOUT,
            ),
            call([msbuild_path, "--version"], stderr=subprocess.STDOUT),
        ],
        any_order=False,
    )


def test_vswhere_install(mock_tools, tmp_path, vswhere_path, msbuild_path):
    """If VSWhere points at a valid MSBuild executable, that executable is
    used."""
    # MSBuild is not on the path; vswhere a valid location, and MSBuild succeeds.
    mock_tools.subprocess.check_output.side_effect = [
        FileNotFoundError,  # MSBuild not on path
        json.dumps(
            [
                {
                    "instanceId": "deadbeef",
                    "installDate": "2022-07-14T10:42:37Z",
                    "installationPath": os.fsdecode(tmp_path / "Visual Studio"),
                }
            ]
        ),  # vswhere returns JSON content
        MSBUILD_OUTPUT,  # MSBuild Succeeds
    ]

    # Verify the installation
    visualstudio = VisualStudio.verify(mock_tools)

    assert visualstudio.msbuild_path == msbuild_path
    assert visualstudio.install_metadata["instanceId"] == "deadbeef"

    # Verification calls are as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [
            call(["MSBuild.exe", "--version"], stderr=subprocess.STDOUT),
            call(
                [vswhere_path, "-latest", "-prerelease", "-format", "json"],
                stderr=subprocess.STDOUT,
            ),
            call([msbuild_path, "--version"], stderr=subprocess.STDOUT),
        ],
        any_order=False,
    )
