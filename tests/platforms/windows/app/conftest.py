import pytest

from ....utils import create_file


# Windows' AppConfig requires attribute 'packaging_format'
@pytest.fixture
def first_app_templated(first_app_config, console_app, tmp_path):
    app_path = tmp_path / "base_path/build/first-app/windows/app/src"

    # Create the stub binary
    exe_name = f"{'Console' if console_app else 'GUI'}-Stub.exe"
    create_file(app_path / exe_name, "Stub binary")

    return first_app_config
