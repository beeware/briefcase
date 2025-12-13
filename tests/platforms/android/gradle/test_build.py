import os
import sys
from subprocess import CalledProcessError
from unittest.mock import MagicMock, PropertyMock

import httpx
import pytest

from briefcase.console import LogLevel
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import AndroidSDK
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.android.gradle import GradleBuildCommand


@pytest.fixture
def build_command(dummy_console, tmp_path, first_app_generated, monkeypatch):
    command = GradleBuildCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.android_sdk = MagicMock(spec_set=AndroidSDK)
    command.tools.os = MagicMock(spec_set=os)
    command.tools.os.environ = {}
    command.tools.sys = MagicMock(spec_set=sys)
    command.tools.httpx = MagicMock(spec_set=httpx)
    command.tools.subprocess = MagicMock(spec_set=Subprocess)
    monkeypatch.setattr(
        type(command.tools), "system_encoding", PropertyMock(return_value="ISO-42")
    )
    return command


def test_unsupported_template_version(build_command, first_app_generated):
    """Error raised if template's target version is not supported."""
    build_command.verify_app = MagicMock(wraps=build_command.verify_app)

    build_command._briefcase_toml.update(
        {first_app_generated: {"briefcase": {"target_version": "0.3.16"}}}
    )

    with pytest.raises(
        BriefcaseCommandError,
        match="The app template used to generate this app is not compatible",
    ):
        build_command(first_app_generated)

    build_command.verify_app.assert_called_once_with(first_app_generated)


@pytest.mark.parametrize(
    ("host_os", "gradlew_name", "tool_debug_mode"),
    [
        ("Windows", "gradlew.bat", True),
        ("Windows", "gradlew.bat", False),
        ("NonWindows", "gradlew", True),
        ("NonWindows", "gradlew", False),
    ],
)
def test_build_app(
    build_command,
    first_app_generated,
    host_os,
    gradlew_name,
    tool_debug_mode,
    tmp_path,
):
    """The app can be built, invoking gradle."""
    # Mock out `host_os` so we can validate which name is used for gradlew.
    build_command.tools.host_os = host_os
    # Enable verbose tool logging
    if tool_debug_mode:
        build_command.tools.console.verbosity = LogLevel.DEEP_DEBUG
    # Create mock environment with `key`, which we expect to be preserved, and
    # `ANDROID_SDK_ROOT`, which we expect to be overwritten.
    build_command.tools.os.environ = {"ANDROID_SDK_ROOT": "somewhere", "key": "value"}
    build_command.build_app(first_app_generated)
    build_command.tools.android_sdk.verify_emulator.assert_called_once_with()
    build_command.tools.subprocess.run.assert_called_once_with(
        [
            build_command.bundle_path(first_app_generated) / gradlew_name,
            "--console",
            "plain",
        ]
        + (["--debug"] if tool_debug_mode else [])
        + ["assembleDebug"],
        cwd=build_command.bundle_path(first_app_generated),
        env=build_command.tools.android_sdk.env,
        check=True,
        encoding="ISO-42",
    )

    # The app metadata contains the app module
    # The app metadata has been rewritten to reference the test module
    with (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "android"
        / "gradle"
        / "res"
        / "briefcase.xml"
    ).open(encoding="utf-8") as f:
        assert (
            f.read()
            == "\n".join(
                [
                    "<resources>",
                    '    <string name="main_module">first_app</string>',
                    "</resources>",
                ]
            )
            + "\n"
        )

    with (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "android"
        / "gradle"
        / "app"
        / "extract-packages.txt"
    ).open(encoding="utf-8") as f:
        assert f.read() == ""


@pytest.mark.parametrize(
    ("host_os", "gradlew_name", "debug_mode"),
    [
        ("Windows", "gradlew.bat", True),
        ("Windows", "gradlew.bat", False),
        ("NonWindows", "gradlew", True),
        ("NonWindows", "gradlew", False),
    ],
)
def test_build_app_test_mode(
    build_command,
    first_app_generated,
    host_os,
    gradlew_name,
    debug_mode,
    tmp_path,
):
    """The app can be built in test mode, invoking gradle and rewriting app metadata."""
    first_app_generated.test_mode = True
    first_app_generated.test_sources = ["my_test_package"]

    # Mock out `host_os` so we can validate which name is used for gradlew.
    build_command.tools.host_os = host_os
    # Enable verbose tool logging
    if debug_mode:
        build_command.tools.console.verbosity = LogLevel.DEEP_DEBUG
    # Create mock environment with `key`, which we expect to be preserved, and
    # `ANDROID_SDK_ROOT`, which we expect to be overwritten.
    build_command.tools.os.environ = {"ANDROID_SDK_ROOT": "somewhere", "key": "value"}
    build_command.build_app(first_app_generated)
    build_command.tools.android_sdk.verify_emulator.assert_called_once_with()
    build_command.tools.subprocess.run.assert_called_once_with(
        [
            build_command.bundle_path(first_app_generated) / gradlew_name,
            "--console",
            "plain",
        ]
        + (["--debug"] if debug_mode else [])
        + ["assembleDebug"],
        cwd=build_command.bundle_path(first_app_generated),
        env=build_command.tools.android_sdk.env,
        check=True,
        encoding="ISO-42",
    )

    # The app metadata contains the app module
    # The app metadata has been rewritten to reference the test module
    with (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "android"
        / "gradle"
        / "res"
        / "briefcase.xml"
    ).open(encoding="utf-8") as f:
        assert (
            f.read()
            == "\n".join(
                [
                    "<resources>",
                    '    <string name="main_module">tests.first_app</string>',
                    "</resources>",
                ]
            )
            + "\n"
        )

    with (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "android"
        / "gradle"
        / "app"
        / "extract-packages.txt"
    ).open(encoding="utf-8") as f:
        assert f.read() == "my_test_package"


extract_packages_params = [
    ([], ""),
    ([""], ""),
    (["one"], "one"),
    (["one/two"], "two"),
    (["one//two"], "two"),
    (["one/two/three"], "three"),
    (["one", "two"], "one\ntwo"),
    (["one", "two", "three"], "one\ntwo\nthree"),
    (["one/two", "three/four"], "two\nfour"),
    (["/leading"], "leading"),
    (["/leading/two"], "two"),
    (["/leading/two/three"], "three"),
    (["trailing/"], "trailing"),
    (["trailing//"], "trailing"),
    (["trailing/two/"], "two"),
]

# Handle differences in UNC path parsing (https://github.com/python/cpython/pull/100351).
extract_packages_params += [
    (
        ["//leading"],
        "" if sys.platform == "win32" and sys.version_info >= (3, 12) else "leading",
    ),
    (
        ["//leading/two"],
        "" if sys.platform == "win32" else "two",
    ),
    (["//leading/two/three"], "three"),
    (["//leading/two/three/four"], "four"),
]

if sys.platform == "win32":
    extract_packages_params += [
        ([path.replace("/", "\\") for path in test_sources], expected)
        for test_sources, expected in extract_packages_params
    ]


@pytest.mark.parametrize(("test_sources", "expected"), extract_packages_params)
def test_extract_packages(
    build_command, first_app_generated, test_sources, expected, tmp_path
):
    first_app_generated.test_sources = test_sources
    build_command.update_app_metadata(first_app_generated)

    with (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "android"
        / "gradle"
        / "app"
        / "extract-packages.txt"
    ).open(encoding="utf-8") as f:
        assert f.read() == expected


def test_extract_packages_debugger(
    build_command, first_app_generated, dummy_debugger, tmp_path
):
    first_app_generated.test_sources = ["one", "two", "three"]
    first_app_generated.debugger = dummy_debugger
    build_command.update_app_metadata(first_app_generated)

    with (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "android"
        / "gradle"
        / "app"
        / "extract-packages.txt"
    ).open(encoding="utf-8") as f:
        assert f.read() == "*"


def test_print_gradle_errors(build_command, first_app_generated):
    """Validate that build_app() will convert stderr/stdout from the process into
    exception text."""
    # Create a mock subprocess that crashes, printing text partly in non-ASCII.
    build_command.tools.subprocess.run.side_effect = CalledProcessError(
        returncode=1,
        cmd=["ignored"],
    )
    with pytest.raises(BriefcaseCommandError):
        build_command.build_app(first_app_generated)
