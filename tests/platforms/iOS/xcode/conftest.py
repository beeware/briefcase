import pytest

from ....utils import create_file, create_plist_file


@pytest.fixture
def first_app_generated(first_app_config, tmp_path):
    # Create the briefcase.toml file
    create_file(
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "ios"
        / "xcode"
        / "briefcase.toml",
        "\n".join(
            [
                "[paths]",
                'app_packages_path="app_packages"',
                'support_path="Support"',
                'info_plist_path="Info.plist"',
                "",
            ],
        ),
    )

    create_plist_file(
        tmp_path / "base_path/build/first-app/ios/xcode/Info.plist",
        {
            "MainModule": "first_app",
        },
    )

    # Create the package-config folders for each platform.
    # We don't need anything in them; they just need to exist.
    xcframework_path = (
        tmp_path / "base_path/build/first-app/ios/xcode/Support/Python.xcframework"
    )

    # Create the XCframeworks's ios-arm64 Info.plist file
    # with a deliberately weird min iOS version
    create_plist_file(
        xcframework_path / "ios-arm64/Python.framework/Info.plist",
        {
            "CFBundleSupportedPlatforms": "iPhoneOS",
            "CFBundleVersion": "3.10.15",
            "MinimumOSVersion": "12.0",
        },
    )
    (xcframework_path / "ios-arm64/platform-config/arm64-iphoneos").mkdir(parents=True)

    (
        xcframework_path
        / "ios-arm64_x86_64-simulator/platform-config/arm64-iphonesimulator"
    ).mkdir(parents=True)
    (
        xcframework_path
        / "ios-arm64_x86_64-simulator/platform-config/x86_64-iphonesimulator"
    ).mkdir(parents=True)

    return first_app_config
