import pytest

from briefcase.config import DraftAppConfig
from briefcase.debuggers.base import (
    BaseDebugger,
    DebuggerConnectionMode,
)

from ..utils import create_file


@pytest.fixture
def first_app_config(tmp_path):
    create_file(tmp_path / "base_path" / "LICENSE", "The Actual First App License")
    return DraftAppConfig(
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
        license="LicenseRef-CustomLicense",
        license_files=["LICENSE"],
    )


@pytest.fixture
def uppercase_app_config():
    return DraftAppConfig(
        app_name="First-App",
        project_name="First Project",
        formal_name="First App",
        author="Megacorp",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app",
        sources=["src/First_App"],
    )


@pytest.fixture
def underscore_app_config():
    return DraftAppConfig(
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
        requires=["foo==1.2.3", "bar>=4.5"],
        test_requires=["pytest"],
    )


class DummyDebugger(BaseDebugger):
    @property
    def name(self) -> str:
        return "dummy"

    @property
    def connection_mode(self) -> DebuggerConnectionMode:
        raise NotImplementedError

    @property
    def debugger_support_pkg(self) -> str:
        raise NotImplementedError


@pytest.fixture
def dummy_debugger():
    """A dummy debugger for testing purposes."""
    return DummyDebugger()
