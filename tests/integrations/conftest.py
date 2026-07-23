import pytest

from briefcase.config import DraftAppConfig

from ..utils import create_file


@pytest.fixture
def first_app_config(tmp_path):
    create_file(tmp_path / "base_path" / "LICENSE", "MIT License")
    return DraftAppConfig(
        app_name="first-app",
        project_name="First Project",
        formal_name="First App",
        author="Megacorp",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app",
        sources=["src/first_app"],
        license="MIT",
        license_files=["LICENSE"],
    )
