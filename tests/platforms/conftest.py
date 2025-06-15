import pytest

from briefcase.config import AppConfig


@pytest.fixture
def first_app_config():
    return AppConfig(
        app_name="first-app",
        project_name="First Project",
        formal_name="First App",
        author="Megacorp",
        author_email="maintainer@example.com",
        url="https://example.com/first-app",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app \\ demonstration",
        sources=["src/first_app"],
        requires=["foo==1.2.3", "bar>=4.5"],
        test_requires=["pytest"],
        license={"file": "LICENSE"},
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
        license={"file": "LICENSE"},
    )


@pytest.fixture()
def underscore_app_config(first_app_config):
    return AppConfig(
        app_name="first_app",
        project_name="First Project",
        formal_name="First App",
        author="Megacorp",
        author_email="maintainer@example.com",
        url="https://example.com/first-app",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app \\ demonstration",
        sources=["src/first_app"],
        license={"file": "LICENSE"},
        requires=["foo==1.2.3", "bar>=4.5"],
        test_requires=["pytest"],
    )
