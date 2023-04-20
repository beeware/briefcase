import pytest


# Windows' AppConfig requires attribute 'packaging_format'
@pytest.fixture
def first_app_config(first_app_config):
    first_app_config.packaging_format = "msi"
    return first_app_config
