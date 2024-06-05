import pytest

from ....utils import create_file


# Windows' AppConfig requires attribute 'packaging_format'
@pytest.fixture
def first_app_templated(first_app_config, tmp_path):
    app_path = tmp_path / "base_path/build/first-app/windows/app/src"

    # Create the stub binary
    create_file(app_path / "Stub.exe", "Stub binary")

    return first_app_config
