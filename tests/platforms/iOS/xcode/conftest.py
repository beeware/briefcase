import pytest

from ....utils import create_file


@pytest.fixture
def first_app_generated(first_app_config, tmp_path):
    # Create the briefcase.toml file
    create_file(
        tmp_path / "base_path" / "iOS" / "Xcode" / "First App" / "briefcase.toml",
        """
[paths]
app_packages_path="app_packages"
support_path="support"
""",
    )
    return first_app_config
