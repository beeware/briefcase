import pytest

from ...utils import create_file


# Windows' AppConfig requires attribute 'packaging_format'
@pytest.fixture
def first_app_config(first_app_config):
    first_app_config.packaging_format = "msi"
    return first_app_config


@pytest.fixture
def external_first_app(first_app_config, tmp_path):
    first_app_config = first_app_config.copy()
    first_app_config.sources = None
    first_app_config.external_package_path = tmp_path / "base_path/external/src"
    first_app_config.external_package_executable_path = "internal/app.exe"

    # Create the binary
    create_file(
        tmp_path / "base_path/external/src/internal/app.exe",
        "external binary",
    )

    return first_app_config
