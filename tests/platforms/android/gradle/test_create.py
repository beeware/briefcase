import sys

import pytest

from briefcase.console import Console, Log
from briefcase.platforms.android.gradle import GradleCreateCommand


@pytest.fixture
def create_command(tmp_path, first_app_config):
    command = GradleCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    return command


def test_support_package_filename(create_command):
    """The Android support package filename has been customized."""
    assert (
        create_command.support_package_filename(52)
        == f"Python-3.{sys.version_info.minor}-Android-support.b52.zip"
    )


@pytest.mark.parametrize(
    "version, build, version_code",
    [
        ("0.1", None, "10000"),
        ("0.1a3", None, "10000"),
        ("1.2", None, "1020000"),
        ("1.2a3", None, "1020000"),
        ("1.2.3", None, "1020300"),
        ("1.2.3a3", None, "1020300"),
        ("1.2.3b4", None, "1020300"),
        ("1.2.3rc5", None, "1020300"),
        ("1.2.3.dev6", None, "1020300"),
        ("1.2.3.post7", None, "1020300"),
        # Date based
        ("2019.1", None, "2019010000"),
        ("2019.18", None, "2019180000"),
        ("2019.4.18", None, "2019041800"),
        # Build number can be injected
        ("0.1", 3, "10003"),
        ("0.1a3", 42, "10042"),
        ("1.2", 42, "1020042"),
        ("1.2a3", 3, "1020003"),
        ("1.2.3", 3, "1020303"),
        ("1.2.3b4", 42, "1020342"),
        ("2019.1", 3, "2019010003"),
        ("2019.1b4", 42, "2019010042"),
    ],
)
def test_version_code(create_command, first_app_config, version, build, version_code):
    """Validate that create adds version_code to the template context."""
    first_app_config.version = version
    if build:
        first_app_config.build = build
    context = create_command.output_format_template_context(first_app_config)
    assert context["version_code"] == version_code
    assert context["safe_formal_name"] == "First App"

    # Version code must be less than a 32-bit signed integer MAXINT.
    assert int(version_code) < 2147483647


extract_packages_params = [
    ([], ""),
    (["one"], '"one"'),
    (["one/two"], '"two"'),
    (["one/two/three"], '"three"'),
    (["one", "two"], '"one", "two"'),
    (["one", "two", "three"], '"one", "two", "three"'),
    (["one/two", "three/four"], '"two", "four"'),
    (["/leading"], '"leading"'),
    (["//leading"], '"leading"'),
    (["/leading/two"], '"two"'),
    (["trailing/"], '"trailing"'),
    (["trailing//"], '"trailing"'),
    (["trailing/two/"], '"two"'),
]
if sys.platform == "win32":
    extract_packages_params += [
        ([path.replace("/", "\\") for path in test_sources], expected)
        for test_sources, expected in extract_packages_params
    ]


@pytest.mark.parametrize("test_sources, expected", extract_packages_params)
def test_extract_packages(create_command, first_app_config, test_sources, expected):
    first_app_config.test_sources = test_sources
    context = create_command.output_format_template_context(first_app_config)
    assert context["extract_packages"] == expected
