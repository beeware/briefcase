import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError, UnsupportedHostError
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


@pytest.mark.parametrize("host_os", ["WeirdOS"])
def test_unsupported_host_os(create_command, host_os):
    """Error raised for an unsupported OS."""
    create_command.tools.host_os = host_os

    with pytest.raises(UnsupportedHostError, match="This command is not supported on"):
        create_command()


def test_unsupported_template_version(create_command, first_app_config):
    """Error raised if template's target version is not supported."""
    # Skip rolling out the template and support package
    create_command.generate_app_template = MagicMock()
    create_command.install_app_support_package = MagicMock()

    # Skip tool verification
    create_command.verify_tools = MagicMock()

    create_command.verify_app = MagicMock(wraps=create_command.verify_app)

    create_command._briefcase_toml.update(
        {first_app_config: {"briefcase": {"target_epoch": "0.3.16"}}}
    )

    with pytest.raises(
        BriefcaseCommandError,
        match="The app template used to generate this app is not compatible",
    ):
        create_command(first_app_config)

    create_command.verify_app.assert_called_once_with(first_app_config)


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


@pytest.mark.parametrize(
    "input, output, has_warning",
    [
        (
            None,
            {
                "implementation": [
                    "androidx.appcompat:appcompat:1.0.2",
                    "androidx.constraintlayout:constraintlayout:1.1.3",
                    "androidx.swiperefreshlayout:swiperefreshlayout:1.1.0",
                ]
            },
            True,
        ),
        (
            [],
            {"implementation": []},
            False,
        ),
        (
            [
                "com.example.foo:foo:1.2.3",
                "com.example.bar:bar:2.3.4",
            ],
            {
                "implementation": [
                    "com.example.foo:foo:1.2.3",
                    "com.example.bar:bar:2.3.4",
                ]
            },
            False,
        ),
    ],
)
def test_build_gradle_dependencies(
    create_command,
    first_app_config,
    input,
    output,
    has_warning,
    capsys,
):
    """Validate that create adds version_code to the template context."""
    if input is not None:
        first_app_config.build_gradle_dependencies = input

    context = create_command.output_format_template_context(first_app_config)
    assert context["build_gradle_dependencies"] == output

    assert (
        "** WARNING: App does not define build_gradle_dependencies              **"
        in capsys.readouterr().out
    ) == has_warning


extract_packages_params = [
    ([], ""),
    ([""], ""),
    (["one"], '"one"'),
    (["one/two"], '"two"'),
    (["one//two"], '"two"'),
    (["one/two/three"], '"three"'),
    (["one", "two"], '"one", "two"'),
    (["one", "two", "three"], '"one", "two", "three"'),
    (["one/two", "three/four"], '"two", "four"'),
    (["/leading"], '"leading"'),
    (["/leading/two"], '"two"'),
    (["/leading/two/three"], '"three"'),
    (["trailing/"], '"trailing"'),
    (["trailing//"], '"trailing"'),
    (["trailing/two/"], '"two"'),
]

# Handle differences in UNC path parsing (https://github.com/python/cpython/pull/100351).
extract_packages_params += [
    (
        ["//leading"],
        "" if sys.platform == "win32" and sys.version_info >= (3, 12) else '"leading"',
    ),
    (
        ["//leading/two"],
        "" if sys.platform == "win32" else '"two"',
    ),
    (["//leading/two/three"], '"three"'),
    (["//leading/two/three/four"], '"four"'),
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


@pytest.mark.parametrize(
    "permissions, features, context",
    [
        # No permissions
        (
            {},
            {},
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                },
                "features": {},
            },
        ),
        # Only custom permissions
        (
            {
                "android.permission.READ_CONTACTS": True,
            },
            {
                "android.hardware.bluetooth": True,
            },
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                    "android.permission.READ_CONTACTS": True,
                },
                "features": {
                    "android.hardware.bluetooth": True,
                },
            },
        ),
        # Camera permissions
        (
            {
                "camera": "I need to see you",
            },
            {},
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                    "android.permission.CAMERA": True,
                },
                "features": {
                    "android.hardware.camera": False,
                    "android.hardware.camera.any": False,
                    "android.hardware.camera.autofocus": False,
                    "android.hardware.camera.external": False,
                    "android.hardware.camera.front": False,
                },
            },
        ),
        # Microphone permissions
        (
            {
                "microphone": "I need to hear you",
            },
            {},
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                    "android.permission.RECORD_AUDIO": True,
                },
                "features": {},
            },
        ),
        # Coarse location permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
            },
            {},
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                    "android.permission.ACCESS_COARSE_LOCATION": True,
                },
                "features": {
                    "android.hardware.location.gps": False,
                    "android.hardware.location.network": False,
                },
            },
        ),
        # Fine location permissions
        (
            {
                "fine_location": "I need to know exactly where you are",
            },
            {},
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                    "android.permission.ACCESS_FINE_LOCATION": True,
                },
                "features": {
                    "android.hardware.location.gps": False,
                    "android.hardware.location.network": False,
                },
            },
        ),
        # Background location permissions
        (
            {
                "background_location": "I always need to know where you are",
            },
            {},
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                    "android.permission.ACCESS_BACKGROUND_LOCATION": True,
                },
                "features": {
                    "android.hardware.location.gps": False,
                    "android.hardware.location.network": False,
                },
            },
        ),
        # Coarse location background permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
                "background_location": "I always need to know where you are",
            },
            {},
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                    "android.permission.ACCESS_COARSE_LOCATION": True,
                    "android.permission.ACCESS_BACKGROUND_LOCATION": True,
                },
                "features": {
                    "android.hardware.location.gps": False,
                    "android.hardware.location.network": False,
                },
            },
        ),
        # Fine location background permissions
        (
            {
                "fine_location": "I need to know exactly where you are",
                "background_location": "I always need to know where you are",
            },
            {},
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                    "android.permission.ACCESS_FINE_LOCATION": True,
                    "android.permission.ACCESS_BACKGROUND_LOCATION": True,
                },
                "features": {
                    "android.hardware.location.gps": False,
                    "android.hardware.location.network": False,
                },
            },
        ),
        # Coarse and fine location permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
                "fine_location": "I need to know exactly where you are",
            },
            {},
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                    "android.permission.ACCESS_COARSE_LOCATION": True,
                    "android.permission.ACCESS_FINE_LOCATION": True,
                },
                "features": {
                    "android.hardware.location.gps": False,
                    "android.hardware.location.network": False,
                },
            },
        ),
        # Coarse and fine background location permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
                "fine_location": "I need to know exactly where you are",
                "background_location": "I always need to know where you are",
            },
            {},
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                    "android.permission.ACCESS_COARSE_LOCATION": True,
                    "android.permission.ACCESS_FINE_LOCATION": True,
                    "android.permission.ACCESS_BACKGROUND_LOCATION": True,
                },
                "features": {
                    "android.hardware.location.gps": False,
                    "android.hardware.location.network": False,
                },
            },
        ),
        # Photo library permissions
        (
            {
                "photo_library": "I need to see your library",
            },
            {},
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                    "android.permission.READ_MEDIA_VISUAL_USER_SELECTED": True,
                },
                "features": {},
            },
        ),
        # Override and augment by cross-platform definitions
        (
            {
                "camera": "I need to see you",
                "android.permission.CAMERA": False,
                "android.permission.READ_CONTACTS": True,
            },
            {
                "android.hardware.camera.external": True,
                "android.hardware.bluetooth": True,
            },
            {
                "permissions": {
                    "android.permission.ACCESS_NETWORK_STATE": True,
                    "android.permission.INTERNET": True,
                    "android.permission.CAMERA": False,
                    "android.permission.READ_CONTACTS": True,
                },
                "features": {
                    "android.hardware.camera": False,
                    "android.hardware.camera.any": False,
                    "android.hardware.camera.autofocus": False,
                    "android.hardware.camera.external": True,
                    "android.hardware.camera.front": False,
                    "android.hardware.bluetooth": True,
                },
            },
        ),
    ],
)
def test_permissions_context(create_command, first_app, permissions, features, context):
    """Platform-specific permissions can be added to the context."""
    # Set the permission and entitlement value
    first_app.permission = permissions
    first_app.feature = features
    # Extract the cross-platform permissions
    x_permissions = create_command._x_permissions(first_app)
    # Check that the final platform permissions are rendered as expected.
    assert context == create_command.permissions_context(first_app, x_permissions)
