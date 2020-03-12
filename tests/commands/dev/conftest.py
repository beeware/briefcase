import pytest
from unittest import mock

from briefcase.commands import DevCommand
from briefcase.config import AppConfig


@pytest.fixture
def dev_command(tmp_path):
    command = DevCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    return command


@pytest.fixture
def first_app_uninstalled(tmp_path):
    # Make sure the source code exists
    (tmp_path / "src" / "first").mkdir(parents=True, exist_ok=True)
    with (tmp_path / "src" / "first" / "__init__.py").open("w") as f:
        f.write('print("Hello world")')

    return AppConfig(
        app_name="first",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app",
        sources=["src/first"],
    )


@pytest.fixture
def first_app(tmp_path, first_app_uninstalled):
    # The same fixture as first_app_uninstalled,
    # but ensures that the .dist-info folder for the app exists
    (tmp_path / "src" / "first.dist-info").mkdir(exist_ok=True)
    return first_app_uninstalled


@pytest.fixture
def second_app(tmp_path):
    # Make sure the source code exists
    (tmp_path / "src" / "second").mkdir(parents=True, exist_ok=True)
    with (tmp_path / "src" / "second" / "__init__.py").open("w") as f:
        f.write('print("Hello world")')

    # Create the dist-info folder
    (tmp_path / "src" / "second.dist-info").mkdir(exist_ok=True)

    return AppConfig(
        app_name="second",
        bundle="com.example",
        version="0.0.2",
        description="The second simple app",
        sources=["src/second"],
    )


@pytest.fixture
def third_app(tmp_path):
    # Make sure the source code exists
    (tmp_path / "src" / "third").mkdir(parents=True, exist_ok=True)
    with (tmp_path / "src" / "third" / "__init__.py").open("w") as f:
        f.write('print("Hello world")')

    # Create the dist-info folder
    (tmp_path / "src" / "third.dist-info").mkdir(exist_ok=True)

    return AppConfig(
        app_name="third",
        bundle="com.example",
        version="0.0.2",
        description="The third simple app",
        sources=["src/third", "src/common", "other"],
    )
