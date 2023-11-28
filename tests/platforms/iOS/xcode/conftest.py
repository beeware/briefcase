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
        """
[paths]
app_packages_path="app_packages"
support_path="support"
info_plist_path="Info.plist"
""",
    )

    create_plist_file(
        tmp_path / "base_path/build/first-app/ios/xcode/Info.plist",
        {
            "MainModule": "first_app",
        },
    )
    return first_app_config
