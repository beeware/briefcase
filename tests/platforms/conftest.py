import pytest

from briefcase.config import AppConfig


@pytest.fixture
def first_app_config():
    return AppConfig(
        app_name="first-app",
        project_name="First Project",
        formal_name="First App",
        author="Megacorp",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app \\ demonstration",
        sources=["src/first_app"],
    )


@pytest.fixture
def uppercase_app_config():
    return AppConfig(
        app_name="First-App",
        project_name="First Project",
        formal_name="First App",
        author="Megacorp",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app",
        sources=["src/First_App"],
    )
